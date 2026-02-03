#!/usr/bin/env python3
"""
Fix all gn-math games to match zones.json exactly by zone ID
"""
import json
import requests
import re
from pathlib import Path

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"
HTML_BASE = "https://cdn.jsdelivr.net/gh/gn-math/html@main/"

def normalize_name(name):
    """Normalize game name for matching"""
    # Remove version numbers, extra info
    name = re.sub(r'\s+v?\d+\.?\d*.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+\(.*?\)', '', name)
    name = re.sub(r'\s+\[.*?\]', '', name)
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def load_zones():
    """Load zones.json"""
    print(f"Fetching zones.json...")
    r = requests.get(ZONES_URL, timeout=30)
    r.raise_for_status()
    zones = r.json()
    print(f"Loaded {len(zones)} zones")
    return zones

def load_games():
    """Load current games.json"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    return games

def match_by_directory_and_zone_id(games, zones):
    """Match games by directory name and zone ID from imagePath"""
    # Create zone lookup by ID
    zone_by_id = {}
    for zone in zones:
        if 'id' in zone and zone['id'] != -1:
            zone_by_id[zone['id']] = zone
    
    # Create zone lookup by normalized name
    zone_by_name = {}
    for zone in zones:
        if 'name' in zone and 'id' in zone and zone['id'] != -1:
            norm_name = normalize_name(zone['name'])
            if norm_name not in zone_by_name:
                zone_by_name[norm_name] = zone
    
    fixed_games = []
    fixed_count = 0
    
    for game in games:
        if game.get('source') != 'non-semag':
            fixed_games.append(game)
            continue
        
        game_name = game.get('name', '')
        game_dir = game.get('directory', '')
        image_path = game.get('imagePath', '')
        
        # Extract zone ID from imagePath if present
        zone_id = None
        if image_path:
            match = re.search(r'/(\d+)\.png', image_path)
            if match:
                zone_id = int(match.group(1))
        
        # Try to find matching zone
        matched_zone = None
        
        # First try by zone ID from imagePath
        if zone_id is not None and zone_id in zone_by_id:
            matched_zone = zone_by_id[zone_id]
            # Verify the name matches (or is close)
            norm_game = normalize_name(game_name)
            norm_zone = normalize_name(matched_zone['name'])
            if norm_game != norm_zone:
                print(f"  ⚠ Zone ID {zone_id} mismatch: '{game_name}' -> '{matched_zone['name']}'")
                # Update to correct name
                game['name'] = matched_zone['name']
                game['directory'] = re.sub(r'[^a-z0-9]+', '-', matched_zone['name'].lower()).strip('-')
                game['imagePath'] = f"{COVERS_BASE}{zone_id}.png"
                fixed_count += 1
        else:
            # Try to match by name
            norm_game = normalize_name(game_name)
            if norm_game in zone_by_name:
                matched_zone = zone_by_name[norm_game]
                zone_id = matched_zone['id']
                # Update imagePath if missing or wrong
                if not image_path or f"/{zone_id}.png" not in image_path:
                    game['imagePath'] = f"{COVERS_BASE}{zone_id}.png"
                    fixed_count += 1
        
        # Special case: Check for "Ragdoll Hit" that should be "Driven Wild"
        if 'ragdoll' in game_name.lower() and 'hit' in game_name.lower():
            # Check if imagePath points to zone 43 (Driven Wild)
            if image_path and '/43.png' in image_path:
                print(f"  Fixing: '{game_name}' is actually 'Driven Wild' (zone 43)")
                if 43 in zone_by_id:
                    game['name'] = zone_by_id[43]['name']
                    game['directory'] = re.sub(r'[^a-z0-9]+', '-', zone_by_id[43]['name'].lower()).strip('-')
                    game['imagePath'] = f"{COVERS_BASE}43.png"
                    fixed_count += 1
            # Or if it should be Ragdoll Hit (zone 44)
            elif 44 in zone_by_id:
                print(f"  Fixing: '{game_name}' should be 'Ragdoll Hit' (zone 44)")
                game['name'] = zone_by_id[44]['name']
                game['directory'] = re.sub(r'[^a-z0-9]+', '-', zone_by_id[44]['name'].lower()).strip('-')
                game['imagePath'] = f"{COVERS_BASE}44.png"
                fixed_count += 1
        
        # Ensure imagePath is set correctly based on zone ID
        if matched_zone and 'id' in matched_zone:
            correct_path = f"{COVERS_BASE}{matched_zone['id']}.png"
            if game.get('imagePath') != correct_path:
                game['imagePath'] = correct_path
        
        fixed_games.append(game)
    
    return fixed_games, fixed_count

def main():
    print("Fixing All GN-Math Game Matches")
    print("=" * 50)
    
    zones = load_zones()
    games = load_games()
    
    print(f"\nCurrent games: {len(games)}")
    non_semag = [g for g in games if g.get('source') == 'non-semag']
    print(f"Non-semag games: {len(non_semag)}")
    
    print("\nFixing matches...")
    fixed_games, fixed_count = match_by_directory_and_zone_id(games, zones)
    
    # Save
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_games, f, indent='\t', ensure_ascii=False)
    
    print(f"\n✓ Fixed {fixed_count} games")
    print(f"✓ Saved to {games_file}")

if __name__ == "__main__":
    main()



