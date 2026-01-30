#!/usr/bin/env python3
"""
Clone a specific game from gn-math.dev by zone ID
"""
import requests
import json
import re
from urllib.parse import urljoin
from pathlib import Path
import sys

ZONES_URL = "https://cdn.jsdelivr.net/gh/gn-math/assets@main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"
HTML_BASE = "https://cdn.jsdelivr.net/gh/gn-math/html@main/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"

def download_file(url, filepath, silent=False):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=15)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        if not silent:
            print(f"    Error downloading {url}: {e}", flush=True)
        return False

def normalize_directory_name(name):
    """Convert game name to directory name"""
    dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return dir_name

def main():
    zone_id = 122
    
    print(f"Cloning game from gn-math.dev (Zone ID: {zone_id})")
    print("=" * 60, flush=True)
    
    # Fetch zones
    print(f"Fetching zones from {ZONES_URL}...", flush=True)
    try:
        r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones_data = r.json()
    except Exception as e:
        print(f"Error fetching zones: {e}", flush=True)
        return
    
    # Find the zone with the specified ID
    zone_data = None
    for zone in zones_data:
        if isinstance(zone, dict) and zone.get('id') == zone_id:
            zone_data = zone
            break
    
    if not zone_data:
        print(f"⚠ Zone ID {zone_id} not found in zones.json!", flush=True)
        return
    
    game_name = zone_data.get('name', f"Zone {zone_id}")
    print(f"\nFound game: {game_name}", flush=True)
    
    # Check if game already exists
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'r', encoding='utf-8') as f:
        existing_games = json.load(f)
    
    dir_name = normalize_directory_name(game_name)
    existing_dirs = {g.get('directory', '') for g in existing_games}
    existing_names = {g.get('name', '').lower() for g in existing_games}
    
    # Check if we should replace existing game
    existing_game = None
    for game in existing_games:
        if game.get('directory') == dir_name or game.get('name', '').lower() == game_name.lower():
            existing_game = game
            break
    
    if existing_game:
        print(f"⚠ Game already exists, will replace it", flush=True)
        print(f"  Name: {game_name}", flush=True)
        print(f"  Directory: {dir_name}", flush=True)
        
        # Remove old entry
        existing_games.remove(existing_game)
        
        # Remove old directory if it exists
        old_dir = GAMES_DIR / dir_name
        if old_dir.exists():
            import shutil
            try:
                shutil.rmtree(old_dir)
                print(f"  Removed old directory", flush=True)
            except Exception as e:
                print(f"  Error removing old directory: {e}", flush=True)
    
    # Download game
    print(f"\nDownloading: {game_name}", flush=True)
    game_dir = GAMES_DIR / dir_name
    
    # Get game HTML URL
    zone_url = zone_data.get('url', '')
    if zone_url and '{HTML_URL}' in zone_url:
        html_url = zone_url.replace('{HTML_URL}', HTML_BASE.rstrip('/'))
    elif zone_url and zone_url.startswith('http'):
        html_url = zone_url
    else:
        html_url = f"{HTML_BASE}{zone_id}/index.html"
    
    # Skip if it's not a game URL
    if html_url.startswith('https://discord.gg') or html_url.startswith('https://discord.com'):
        print(f"  ⏭ Skipping (not a game URL)", flush=True)
        return
    
    # Download HTML
    html_file = game_dir / "index.html"
    if not download_file(html_url, html_file):
        print(f"    ⚠ Could not download HTML, trying alternatives...", flush=True)
        alternatives = [
            f"{HTML_BASE}{zone_id}.html",
            f"{HTML_BASE}{zone_id}/index.html",
            f"{HTML_BASE}{zone_id}-a.html",
        ]
        downloaded = False
        for alt_url in alternatives:
            if download_file(alt_url, html_file):
                downloaded = True
                break
        if not downloaded:
            print(f"  ✗ Failed to download HTML", flush=True)
            return
    
    print(f"  ✓ Downloaded HTML", flush=True)
    
    # Download cover image
    cover_url = f"{COVERS_BASE}{zone_id}.png"
    cover_file = game_dir / "cover.png"
    if download_file(cover_url, cover_file, silent=True):
        print(f"  ✓ Downloaded cover image", flush=True)
    else:
        print(f"  ⚠ Could not download cover image", flush=True)
    
    # Add to games.json
    game_info = {
        'name': game_name,
        'directory': dir_name,
        'image': 'cover.png',
        'source': 'non-semag',
        'imagePath': f"{COVERS_BASE}{zone_id}.png"
    }
    
    existing_games.append(game_info)
    
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(existing_games, f, indent='\t', ensure_ascii=False)
    
    print(f"\n" + "=" * 60, flush=True)
    print(f"SUCCESS", flush=True)
    print(f"=" * 60, flush=True)
    print(f"✓ Downloaded: {game_name}", flush=True)
    print(f"✓ Directory: {dir_name}", flush=True)
    print(f"✓ Added to games.json", flush=True)
    print(f"✓ Total games in database: {len(existing_games)}", flush=True)

if __name__ == "__main__":
    main()

