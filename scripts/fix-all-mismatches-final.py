#!/usr/bin/env python3
"""
Fix all mismatches based on actual directory contents and zones.json
"""
import json
import requests
from pathlib import Path
import re

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"

def load_zones():
    r = requests.get(ZONES_URL, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    zones = load_zones()
    
    # Create zone lookup
    zone_by_id = {z['id']: z for z in zones if 'id' in z and z['id'] != -1}
    
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print("Fixing all mismatches based on zones.json...")
    
    # Known directory corrections based on actual file contents
    directory_corrections = {
        'ragdoll-hit': {'name': 'Driven Wild', 'zone_id': 43},
        'driven-wild': {'name': 'Road of Fury', 'zone_id': 42},  # Contains roadoffury.swf
    }
    
    fixed_count = 0
    fixed_games = []
    seen_dirs = set()
    
    for game in games:
        if game.get('source') != 'non-semag':
            fixed_games.append(game)
            continue
        
        game_dir = game.get('directory', '')
        game_name = game.get('name', '')
        
        # Check for known corrections
        if game_dir in directory_corrections:
            correction = directory_corrections[game_dir]
            if game_name != correction['name']:
                print(f"  Fixing {game_dir}: '{game_name}' -> '{correction['name']}' (zone {correction['zone_id']})")
                game['name'] = correction['name']
                game['imagePath'] = f"{COVERS_BASE}{correction['zone_id']}.png"
                fixed_count += 1
        
        # Remove duplicates - keep first occurrence of each directory
        if game_dir in seen_dirs:
            print(f"  Removing duplicate: {game_name} ({game_dir})")
            continue
        
        seen_dirs.add(game_dir)
        
        # Ensure imagePath matches zone ID from zones.json
        image_path = game.get('imagePath', '')
        if image_path:
            match = re.search(r'/(\d+)\.png', image_path)
            if match:
                zone_id = int(match.group(1))
                if zone_id in zone_by_id:
                    correct_name = zone_by_id[zone_id]['name']
                    if game_name != correct_name:
                        print(f"  Updating name by zone ID {zone_id}: '{game_name}' -> '{correct_name}'")
                        game['name'] = correct_name
                        game['directory'] = re.sub(r'[^a-z0-9]+', '-', correct_name.lower()).strip('-')
                        fixed_count += 1
        
        fixed_games.append(game)
    
    # Save
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_games, f, indent='\t', ensure_ascii=False)
    
    print(f"\n✓ Fixed {fixed_count} games")
    print(f"✓ Total games: {len(fixed_games)}")

if __name__ == "__main__":
    main()



