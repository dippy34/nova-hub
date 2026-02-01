#!/usr/bin/env python3
"""
Scrape 50 games from gn-math.dev (no duplicates, with progress)
"""
import requests
import json
import re
from urllib.parse import urljoin
from pathlib import Path
import time
import sys

ZONES_URL = "https://cdn.jsdelivr.net/gh/gn-math/assets@main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"
HTML_BASE = "https://cdn.jsdelivr.net/gh/gn-math/html@main/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
MAX_GAMES = 100

def download_file(url, filepath, silent=False):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        if not silent:
            pass  # Errors are handled in calling function
        return False

def load_existing_games():
    """Load existing games to avoid duplicates"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    if games_file.exists():
        with open(games_file, 'r', encoding='utf-8') as f:
            games = json.load(f)
            existing_dirs = {g.get('directory', '') for g in games}
            existing_names = {g.get('name', '').lower() for g in games}
            return existing_dirs, existing_names, games
    return set(), set(), []

def normalize_directory_name(name):
    """Convert game name to directory name"""
    dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    if not dir_name or len(dir_name) < 2:
        return None
    return dir_name

def download_game(zone_id, zone_data, game_dir):
    """Download a single game locally"""
    # Get game HTML URL from zones.json
    zone_url = zone_data.get('url', '') if isinstance(zone_data, dict) else ''
    if zone_url and '{HTML_URL}' in zone_url:
        html_url = zone_url.replace('{HTML_URL}', HTML_BASE.rstrip('/'))
    elif zone_url and zone_url.startswith('http'):
        html_url = zone_url
    else:
        html_url = f"{HTML_BASE}{zone_id}/index.html"
    
    # Skip if it's not a game URL (like Discord links)
    if html_url.startswith('https://discord.gg') or html_url.startswith('https://discord.com'):
        return False
    
    # Try to download the HTML
    html_file = game_dir / "index.html"
    if not download_file(html_url, html_file, silent=True):
        # Try common alternatives
        alternatives = [
            f"{HTML_BASE}{zone_id}.html",
            f"{HTML_BASE}{zone_id}/index.html",
            f"{HTML_BASE}{zone_id}-a.html",
        ]
        downloaded = False
        for alt_url in alternatives:
            if download_file(alt_url, html_file, silent=True):
                downloaded = True
                break
        if not downloaded:
            return False
    
    # Download cover image
    cover_url = f"{COVERS_BASE}{zone_id}.png"
    cover_file = game_dir / "cover.png"
    download_file(cover_url, cover_file, silent=True)
    
    return True

def main():
    print("GN-Math.dev Game Scraper (100 games)")
    print("=" * 60, flush=True)
    
    # Load existing games
    print("Loading existing games...", flush=True)
    existing_dirs, existing_names, existing_games = load_existing_games()
    print(f"Found {len(existing_games)} existing games in database", flush=True)
    
    # Fetch zones
    print(f"\nFetching zones from {ZONES_URL}...", flush=True)
    try:
        r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones_data = r.json()
    except Exception as e:
        print(f"Error fetching zones: {e}", flush=True)
        return
    
    print(f"Found {len(zones_data)} total zones", flush=True)
    
    # Filter out games that already exist and skip special entries
    available_zones = []
    for zone_data in zones_data:
        if not isinstance(zone_data, dict):
            continue
            
        zone_id = zone_data.get('id')
        name = zone_data.get('name') or f"Zone {zone_id}"
        
        # Skip suggestion/comments entries
        if name.startswith('[!]') or 'suggest' in name.lower() or 'comment' in name.lower():
            continue
        
        dir_name = normalize_directory_name(name)
        if not dir_name:
            continue
        
        if name.lower() not in existing_names and dir_name not in existing_dirs:
            available_zones.append((zone_id, zone_data, name, dir_name))
    
    print(f"\nFound {len(available_zones)} available games (not in database)", flush=True)
    
    if not available_zones:
        print("\nAll games are already in your database!", flush=True)
        return
    
    # Limit to MAX_GAMES
    games_to_download = min(MAX_GAMES, len(available_zones))
    print(f"Downloading first {games_to_download} games...\n", flush=True)
    
    downloaded_games = []
    failed_games = []
    
    for i, (zone_id, zone_data, name, dir_name) in enumerate(available_zones[:games_to_download], 1):
        game_dir = GAMES_DIR / dir_name
        
        # Progress display
        progress = f"[{i}/{games_to_download}]"
        percentage = int((i / games_to_download) * 100)
        bar_length = 30
        filled = int(bar_length * i / games_to_download)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"{progress} ({percentage:3d}%) |{bar}| {name}", flush=True)
        
        try:
            if download_game(zone_id, zone_data, game_dir):
                game_info = {
                    'name': name,
                    'directory': dir_name,
                    'image': 'cover.png',
                    'source': 'non-semag',
                    'imagePath': f"{COVERS_BASE}{zone_id}.png"
                }
                downloaded_games.append(game_info)
                print(f"      ✓ Success", flush=True)
            else:
                failed_games.append(name)
                print(f"      ✗ Failed to download", flush=True)
        except Exception as e:
            failed_games.append(name)
            print(f"      ✗ Error: {str(e)[:50]}", flush=True)
            continue
        
        time.sleep(0.3)  # Be polite
    
    # Add to games.json
    print("\n" + "=" * 60, flush=True)
    print("DOWNLOAD SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"Successfully downloaded: {len(downloaded_games)}/{games_to_download}", flush=True)
    print(f"Failed: {len(failed_games)}/{games_to_download}", flush=True)
    
    if downloaded_games:
        existing_games.extend(downloaded_games)
        games_file = Path(__file__).parent.parent / "data" / "games.json"
        
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n✓ Added {len(downloaded_games)} games to games.json", flush=True)
        print(f"✓ Total games in database: {len(existing_games)}", flush=True)
    else:
        print("\n⚠ No games were successfully downloaded", flush=True)
    
    if failed_games:
        print(f"\nFailed games ({len(failed_games)}):", flush=True)
        for name in failed_games[:10]:  # Show first 10
            print(f"  - {name}", flush=True)
        if len(failed_games) > 10:
            print(f"  ... and {len(failed_games) - 10} more", flush=True)

if __name__ == "__main__":
    main()

