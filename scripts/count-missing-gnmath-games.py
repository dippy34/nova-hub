#!/usr/bin/env python3
"""
Count how many games from gn-math.dev are missing from local database
"""
import requests
import json
import re
from pathlib import Path

ZONES_URL = "https://cdn.jsdelivr.net/gh/gn-math/assets@main/zones.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

def normalize_directory_name(name):
    """Convert game name to directory name"""
    dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    if not dir_name or len(dir_name) < 2:
        return None
    return dir_name

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

def main():
    print("Checking missing games from gn-math.dev...")
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
    
    print(f"Found {len(zones_data)} total zones in gn-math.dev", flush=True)
    
    # Filter out games that already exist and skip special entries
    missing_games = []
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
            missing_games.append((zone_id, name))
    
    print(f"\n" + "=" * 60, flush=True)
    print(f"MISSING GAMES COUNT", flush=True)
    print("=" * 60, flush=True)
    print(f"Total zones in gn-math.dev: {len(zones_data)}", flush=True)
    print(f"Games you already have: {len(zones_data) - len(missing_games)}", flush=True)
    print(f"Games you DON'T have: {len(missing_games)}", flush=True)
    
    if missing_games:
        print(f"\nFirst 20 missing games:", flush=True)
        for i, (zone_id, name) in enumerate(missing_games[:20], 1):
            print(f"  {i}. {name} (ID: {zone_id})", flush=True)
        if len(missing_games) > 20:
            print(f"  ... and {len(missing_games) - 20} more", flush=True)

if __name__ == "__main__":
    main()

