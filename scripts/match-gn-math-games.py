#!/usr/bin/env python3
"""
Match and fix games from gn-math.dev with the correct metadata
"""
import json
import requests
import re
from pathlib import Path
from urllib.parse import urljoin

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"

def normalize_name(name):
    """Normalize game name for matching"""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def load_zones():
    """Load zones.json from gn-math.dev"""
    print(f"Fetching zones.json from {ZONES_URL}...")
    r = requests.get(ZONES_URL, timeout=30)
    r.raise_for_status()
    zones = r.json()
    print(f"Loaded {len(zones)} zones from gn-math.dev")
    return zones

def load_games():
    """Load current games.json"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    return games

def match_games(games, zones):
    """Match games with zones and update metadata"""
    # Create lookup maps
    zone_by_id = {zone['id']: zone for zone in zones if 'id' in zone}
    zone_by_name = {}
    for zone in zones:
        if 'name' in zone:
            norm_name = normalize_name(zone['name'])
            if norm_name not in zone_by_name:
                zone_by_name[norm_name] = zone
    
    updated_count = 0
    matched_games = []
    
    for game in games:
        if game.get('source') != 'non-semag':
            matched_games.append(game)
            continue
        
        game_name = game.get('name', '')
        norm_game_name = normalize_name(game_name)
        
        # Try to find matching zone
        matched_zone = None
        
        # First try exact name match
        if norm_game_name in zone_by_name:
            matched_zone = zone_by_name[norm_game_name]
        else:
            # Try partial match
            for zone_name, zone in zone_by_name.items():
                if norm_game_name in zone_name or zone_name in norm_game_name:
                    matched_zone = zone
                    break
        
        if matched_zone:
            # Update game with correct metadata
            zone_id = matched_zone.get('id', '')
            zone_name = matched_zone.get('name', game_name)
            
            # Update name if different
            if game_name != zone_name:
                print(f"  Updating name: '{game_name}' -> '{zone_name}'")
                game['name'] = zone_name
            
            # Update directory to match zone ID or normalized name
            new_dir = re.sub(r'[^a-z0-9]+', '-', zone_name.lower()).strip('-')
            if not new_dir or len(new_dir) < 2:
                new_dir = f"zone-{zone_id}" if zone_id else game.get('directory', '')
            
            if game.get('directory') != new_dir:
                print(f"  Updating directory: '{game.get('directory')}' -> '{new_dir}'")
                game['directory'] = new_dir
            
            # Update cover image to use correct zone ID
            if zone_id is not None and zone_id != -1:
                cover_url = f"{COVERS_BASE}{zone_id}.png"
                game['imagePath'] = cover_url
                print(f"  Updated cover: {cover_url}")
            
            updated_count += 1
        else:
            print(f"  ⚠ No match found for: {game_name}")
        
        matched_games.append(game)
    
    return matched_games, updated_count

def main():
    print("GN-Math Game Matcher")
    print("=" * 50)
    
    # Load data
    zones = load_zones()
    games = load_games()
    
    print(f"\nCurrent games: {len(games)}")
    non_semag = [g for g in games if g.get('source') == 'non-semag']
    print(f"Non-semag games: {len(non_semag)}")
    
    # Match and update
    print("\nMatching games...")
    matched_games, updated_count = match_games(games, zones)
    
    # Save updated games.json
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(matched_games, f, indent='\t', ensure_ascii=False)
    
    print(f"\n✓ Updated {updated_count} games")
    print(f"✓ Saved to {games_file}")

if __name__ == "__main__":
    main()



