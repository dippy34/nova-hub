#!/usr/bin/env python3
"""
Download all featured zones from gn-math.dev
"""
import requests
import json
import re
from pathlib import Path
import time
import sys

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"
HTML_BASE = "https://cdn.jsdelivr.net/gh/gn-math/html@main/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def load_existing_games():
    """Load existing games to avoid duplicates"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    if games_file.exists():
        with open(games_file, 'r', encoding='utf-8') as f:
            games = json.load(f)
            existing_dirs = {g.get('directory', '') for g in games}
            existing_names = {g.get('name', '').lower() for g in games}
            return existing_dirs, existing_names
    return set(), set()

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
            pass
        return False

def download_game(zone_id, zone_data, game_dir):
    """Download a single featured game locally"""
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
    if not download_file(html_url, html_file):
        # Try common alternatives
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
            return False
    
    # Download cover image
    cover_url = f"{COVERS_BASE}{zone_id}.png"
    cover_file = game_dir / "cover.png"
    download_file(cover_url, cover_file)
    
    return True

def main():
    print("GN-Math Featured Zones Downloader")
    print("=" * 60)
    
    # Load zones
    print(f"Fetching zones from {ZONES_URL}...")
    try:
        r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones_data = r.json()
    except Exception as e:
        print(f"Error fetching zones: {e}")
        return
    
    # Filter for featured zones
    featured_zones = []
    for zone in zones_data:
        if isinstance(zone, dict) and zone.get('featured') and zone.get('id') != -1:
            featured_zones.append(zone)
    
    print(f"Found {len(featured_zones)} featured zones\n")
    
    existing_dirs, existing_names = load_existing_games()
    
    # Filter out games that already exist
    available_zones = []
    for zone in featured_zones:
        name = zone.get('name', f"Zone {zone.get('id')}")
        dir_name = slugify(name)
        if not dir_name or len(dir_name) < 2:
            dir_name = f"zone-{zone.get('id')}"
        
        if name.lower() not in existing_names and dir_name not in existing_dirs:
            available_zones.append((zone.get('id'), zone, name, dir_name))
        else:
            print(f"  ⏭ Skipping (already exists): {name}")
    
    total_to_download = len(available_zones)
    print(f"\nDownloading {total_to_download} featured zones...\n")
    
    downloaded_games = []
    failed_games = []
    
    for i, (zone_id, zone_data, name, dir_name) in enumerate(available_zones, 1):
        game_dir = GAMES_DIR / dir_name
        progress = f"[{i}/{total_to_download}]"
        percentage = int((i / total_to_download) * 100) if total_to_download > 0 else 0
        
        print(f"{progress} ({percentage}%) Downloading: {name}", flush=True)
        sys.stdout.flush()
        
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
                print(f"  Success: {name}", flush=True)
            else:
                failed_games.append(name)
                print(f"  Failed: {name}", flush=True)
        except Exception as e:
            failed_games.append(name)
            print(f"  Error: {name} - {e}", flush=True)
            continue
        
        time.sleep(0.5)  # Be polite
    
    # Add to games.json
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Successfully downloaded: {len(downloaded_games)}/{total_to_download}")
    print(f"Failed: {len(failed_games)}/{total_to_download}")
    
    if downloaded_games:
        games_file = Path(__file__).parent.parent / "data" / "games.json"
        with open(games_file, 'r', encoding='utf-8') as f:
            existing_games = json.load(f)
        
        existing_games.extend(downloaded_games)
        
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n✓ Added {len(downloaded_games)} featured zones to games.json")
        print(f"✓ Total games in database: {len(existing_games)}")
    else:
        print("\n⚠ No featured zones were successfully downloaded")
    
    if failed_games:
        print(f"\nFailed zones ({len(failed_games)}):")
        for name in failed_games[:10]:
            print(f"  - {name}")
        if len(failed_games) > 10:
            print(f"  ... and {len(failed_games) - 10} more")

if __name__ == "__main__":
    main()


