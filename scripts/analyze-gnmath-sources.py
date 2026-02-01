#!/usr/bin/env python3
"""
Analyze how many games came from gn-math.dev vs already had but gn-math also has
"""
import json
import requests
import re
from pathlib import Path
from collections import defaultdict

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

def extract_zone_id_from_imagepath(imagepath):
    """Extract zone ID from imagePath"""
    if not imagepath:
        return None
    match = re.search(r'/(\d+)\.png$', imagepath)
    if match:
        return int(match.group(1))
    return None

def normalize_name(name):
    """Normalize game name for comparison"""
    if not name:
        return ""
    return name.lower().strip()

def main():
    print("Analyzing gn-math.dev game sources...")
    print("=" * 60, flush=True)
    
    # Load games
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    if not games_file.exists():
        print("games.json not found!")
        return
    
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print(f"Total games in database: {len(games)}", flush=True)
    
    # Fetch zones
    print(f"\nFetching zones from {ZONES_URL}...", flush=True)
    try:
        r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones_data = r.json()
    except Exception as e:
        print(f"Error fetching zones: {e}", flush=True)
        return
    
    # Create zone lookup
    zones_by_id = {}
    zones_by_name_lower = {}
    
    for zone in zones_data:
        if isinstance(zone, dict) and 'id' in zone and zone['id'] != -1:
            zone_id = zone['id']
            zones_by_id[zone_id] = zone
            if 'name' in zone:
                zones_by_name_lower[normalize_name(zone['name'])] = zone
    
    print(f"Total zones in gn-math.dev: {len(zones_by_id)}", flush=True)
    
    # Categorize games
    from_gnmath = []  # Games that came from gn-math (have gn-math imagePath)
    already_had_but_gnmath_has = []  # Games that existed before but gn-math also has
    not_in_gnmath = []  # Games not in gn-math
    
    for game in games:
        imagepath = game.get('imagePath', '')
        game_name = normalize_name(game.get('name', ''))
        
        # Check if it's a gn-math game by imagePath
        zone_id = extract_zone_id_from_imagepath(imagepath)
        is_gnmath_by_path = zone_id is not None and zone_id in zones_by_id
        
        # Check if gn-math has this game by name
        is_in_gnmath_by_name = game_name in zones_by_name_lower
        
        if is_gnmath_by_path:
            # This game came from gn-math (has gn-math cover image)
            from_gnmath.append(game)
        elif is_in_gnmath_by_name:
            # This game exists in gn-math but we had it from another source
            already_had_but_gnmath_has.append(game)
        else:
            # Not in gn-math at all
            not_in_gnmath.append(game)
    
    # Print results
    print("\n" + "=" * 60, flush=True)
    print("ANALYSIS RESULTS", flush=True)
    print("=" * 60, flush=True)
    
    print(f"\n1. Games FROM gn-math.dev:", flush=True)
    print(f"   Count: {len(from_gnmath)}", flush=True)
    print(f"   These are games you scraped/downloaded from gn-math.dev", flush=True)
    
    print(f"\n2. Games you ALREADY HAD but gn-math.dev also has:", flush=True)
    print(f"   Count: {len(already_had_but_gnmath_has)}", flush=True)
    print(f"   These are games you had from other sources (Lagged, etc.)", flush=True)
    print(f"   but gn-math.dev also has them", flush=True)
    
    print(f"\n3. Games NOT in gn-math.dev:", flush=True)
    print(f"   Count: {len(not_in_gnmath)}", flush=True)
    print(f"   These are games from other sources that gn-math.dev doesn't have", flush=True)
    
    print(f"\n4. Total games in gn-math.dev that you have:", flush=True)
    print(f"   Count: {len(from_gnmath) + len(already_had_but_gnmath_has)}", flush=True)
    print(f"   (Games from gn-math + games you had that gn-math also has)", flush=True)
    
    # Show some examples
    if already_had_but_gnmath_has:
        print(f"\nExamples of games you already had but gn-math also has (first 10):", flush=True)
        for i, game in enumerate(already_had_but_gnmath_has[:10], 1):
            print(f"   {i}. {game.get('name', 'N/A')}", flush=True)
        if len(already_had_but_gnmath_has) > 10:
            print(f"   ... and {len(already_had_but_gnmath_has) - 10} more", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"Total games: {len(games)}", flush=True)
    print(f"  ├─ From gn-math.dev: {len(from_gnmath)} ({len(from_gnmath)/len(games)*100:.1f}%)", flush=True)
    print(f"  ├─ Already had (gn-math also has): {len(already_had_but_gnmath_has)} ({len(already_had_but_gnmath_has)/len(games)*100:.1f}%)", flush=True)
    print(f"  └─ Not in gn-math: {len(not_in_gnmath)} ({len(not_in_gnmath)/len(games)*100:.1f}%)", flush=True)

if __name__ == "__main__":
    main()

