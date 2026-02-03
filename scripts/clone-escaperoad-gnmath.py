#!/usr/bin/env python3
"""
Remove all Escape Road games and clone them from gn-math.dev
"""
import requests
import json
import re
from urllib.parse import urljoin
from pathlib import Path
import time
import sys
import shutil

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

def remove_escape_road_games():
    """Remove all Escape Road games from games.json and their directories"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    games_to_remove = []
    for game in games:
        name = game.get('name', '').lower()
        if 'escape road' in name:
            games_to_remove.append(game)
            print(f"  Will remove: {game.get('name')} ({game.get('directory')})", flush=True)
    
    # Remove from games list
    for game in games_to_remove:
        games.remove(game)
        
        # Remove directory
        old_dir = GAMES_DIR / game.get('directory', '')
        if old_dir.exists():
            try:
                shutil.rmtree(old_dir)
                print(f"  Removed directory: {game.get('directory')}", flush=True)
            except Exception as e:
                print(f"  Error removing directory {game.get('directory')}: {e}", flush=True)
    
    # Save updated games.json
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print(f"\nRemoved {len(games_to_remove)} Escape Road games", flush=True)
    return games

def find_escape_road_zones(zones_data):
    """Find all Escape Road games in zones.json"""
    escape_road_zones = []
    
    for zone in zones_data:
        if isinstance(zone, dict):
            name = zone.get('name', '').lower()
            if 'escape' in name and 'road' in name:
                escape_road_zones.append(zone)
                print(f"  Found: {zone.get('name')} (ID: {zone.get('id')})", flush=True)
    
    return escape_road_zones

def download_game(zone_id, zone_data, game_dir, progress_current, progress_total):
    """Download a single game locally"""
    game_name = zone_data.get('name', zone_id)
    print(f"[{progress_current}/{progress_total}] ({progress_current/progress_total:.0%}) Downloading: {game_name}", flush=True)
    
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
        print(f"  ⏭ Skipping (not a game URL)", flush=True)
        return False
    
    # Try to download the HTML
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
            print(f"  ✗ Failed to download HTML for {game_name}", flush=True)
            return False
    
    # Download cover image
    cover_url = f"{COVERS_BASE}{zone_id}.png"
    cover_file = game_dir / "cover.png"
    if download_file(cover_url, cover_file, silent=True):
        print(f"  ✓ Downloaded cover image", flush=True)
    else:
        print(f"  ⚠ Could not download cover image for {game_name}", flush=True)
    
    print(f"  Success: {game_name}", flush=True)
    return True

def normalize_directory_name(name):
    """Convert game name to directory name"""
    dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return dir_name

def main():
    print("Escape Road Games Cloner from gn-math.dev")
    print("=" * 60, flush=True)
    
    # Step 1: Remove existing Escape Road games
    print("\nStep 1: Removing existing Escape Road games...", flush=True)
    existing_games = remove_escape_road_games()
    
    # Step 2: Fetch zones from gn-math.dev
    print(f"\nStep 2: Fetching zones from {ZONES_URL}...", flush=True)
    try:
        r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones_data = r.json()
    except Exception as e:
        print(f"Error fetching zones: {e}", flush=True)
        return
    
    # Step 3: Find Escape Road games
    print("\nStep 3: Finding Escape Road games in zones...", flush=True)
    escape_road_zones = find_escape_road_zones(zones_data)
    
    if not escape_road_zones:
        print("⚠ No Escape Road games found in gn-math.dev!", flush=True)
        return
    
    print(f"\nFound {len(escape_road_zones)} Escape Road games", flush=True)
    
    # Step 4: Download games
    print(f"\nStep 4: Downloading {len(escape_road_zones)} Escape Road games...", flush=True)
    downloaded_games = []
    
    for i, zone_data in enumerate(escape_road_zones, 1):
        zone_id = zone_data.get('id')
        game_name = zone_data.get('name', f"Zone {zone_id}")
        dir_name = normalize_directory_name(game_name)
        game_dir = GAMES_DIR / dir_name
        
        try:
            if download_game(zone_id, zone_data, game_dir, i, len(escape_road_zones)):
                game_info = {
                    'name': game_name,
                    'directory': dir_name,
                    'image': 'cover.png',
                    'source': 'non-semag',
                    'imagePath': f"{COVERS_BASE}{zone_id}.png"
                }
                downloaded_games.append(game_info)
        except Exception as e:
            print(f"  Error downloading {game_name}: {e}", flush=True)
            continue
        
        time.sleep(0.5)  # Be polite
    
    # Step 5: Add to games.json
    if downloaded_games:
        existing_games.extend(downloaded_games)
        games_file = Path(__file__).parent.parent / "data" / "games.json"
        
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n" + "=" * 60, flush=True)
        print(f"DOWNLOAD SUMMARY", flush=True)
        print(f"=" * 60, flush=True)
        print(f"Downloaded new games: {len(downloaded_games)}/{len(escape_road_zones)}", flush=True)
        print(f"✓ Updated games.json", flush=True)
        print(f"✓ Total games in database: {len(existing_games)}", flush=True)
    else:
        print("\n⚠ No games were successfully downloaded", flush=True)

if __name__ == "__main__":
    main()


