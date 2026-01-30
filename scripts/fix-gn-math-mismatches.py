#!/usr/bin/env python3
"""
Fix mismatched games by using zone IDs more carefully
"""
import json
import requests
import re
from pathlib import Path

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"

def normalize_name(name):
    """Normalize game name for matching"""
    # Remove version numbers and extra info
    name = re.sub(r'\s+v?\d+\.?\d*.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+\(.*?\)', '', name)
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def load_zones():
    """Load zones.json from gn-math.dev"""
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

def find_zone_by_id(zones, zone_id):
    """Find zone by ID"""
    for zone in zones:
        if zone.get('id') == zone_id:
            return zone
    return None

def match_games_precisely(games, zones):
    """Match games more precisely using multiple strategies"""
    # Create lookup maps
    zone_by_id = {zone['id']: zone for zone in zones if 'id' in zone and zone['id'] != -1}
    
    # Create name variations map
    zone_by_name_variations = {}
    for zone in zones:
        if 'name' in zone and 'id' in zone and zone['id'] != -1:
            name = zone['name']
            # Store multiple variations
            variations = [
                normalize_name(name),
                normalize_name(name.split('(')[0]),  # Remove parenthetical
                normalize_name(name.split('[')[0]),  # Remove brackets
                normalize_name(re.sub(r'\s+v?\d+.*', '', name)),  # Remove version
            ]
            for var in variations:
                if var and var not in zone_by_name_variations:
                    zone_by_name_variations[var] = zone
    
    # Known corrections
    corrections = {
        'ragdoll-hit': 43,  # Ragdoll Hit
        'driven-wild': 42,  # Driven Wild
    }
    
    updated_count = 0
    fixed_games = []
    
    for game in games:
        if game.get('source') != 'non-semag':
            fixed_games.append(game)
            continue
        
        game_name = game.get('name', '')
        game_dir = game.get('directory', '')
        
        # Check if we have a known correction for this directory
        if game_dir in corrections:
            zone_id = corrections[game_dir]
            matched_zone = find_zone_by_id(zones, zone_id)
            if matched_zone:
                print(f"  Fixing {game_name} (dir: {game_dir}) -> Zone ID {zone_id}: {matched_zone['name']}")
                game['name'] = matched_zone['name']
                game['directory'] = re.sub(r'[^a-z0-9]+', '-', matched_zone['name'].lower()).strip('-')
                game['imagePath'] = f"{COVERS_BASE}{zone_id}.png"
                updated_count += 1
                fixed_games.append(game)
                continue
        
        # Try to match by name
        norm_game_name = normalize_name(game_name)
        matched_zone = None
        
        # Try exact match first
        if norm_game_name in zone_by_name_variations:
            matched_zone = zone_by_name_variations[norm_game_name]
        else:
            # Try partial matches
            for var_name, zone in zone_by_name_variations.items():
                if norm_game_name in var_name or var_name in norm_game_name:
                    # Check if it's a reasonable match (at least 50% overlap)
                    if len(set(norm_game_name) & set(var_name)) / max(len(norm_game_name), len(var_name)) > 0.5:
                        matched_zone = zone
                        break
        
        if matched_zone:
            zone_id = matched_zone.get('id')
            zone_name = matched_zone.get('name', game_name)
            
            # Only update if name is significantly different
            if normalize_name(game_name) != normalize_name(zone_name):
                print(f"  Updating: '{game_name}' -> '{zone_name}' (ID: {zone_id})")
                game['name'] = zone_name
                updated_count += 1
            
            if zone_id is not None:
                game['imagePath'] = f"{COVERS_BASE}{zone_id}.png"
        else:
            print(f"  ⚠ No match for: {game_name} ({game_dir})")
        
        fixed_games.append(game)
    
    return fixed_games, updated_count

def main():
    print("Fixing GN-Math Game Mismatches")
    print("=" * 50)
    
    zones = load_zones()
    games = load_games()
    
    print(f"\nFixing games...")
    fixed_games, updated_count = match_games_precisely(games, zones)
    
    # Save
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_games, f, indent='\t', ensure_ascii=False)
    
    print(f"\n✓ Fixed {updated_count} games")
    print(f"✓ Saved to {games_file}")

if __name__ == "__main__":
    main()


