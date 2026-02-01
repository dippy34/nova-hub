#!/usr/bin/env python3
"""
Match all gn-math games with zones.json to update names and cover images
"""
import json
import requests
import re
from pathlib import Path

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

def load_zones():
    """Load zones.json"""
    print("Fetching zones.json from GitHub...")
    try:
        r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones = r.json()
        print(f"Loaded {len(zones)} zones")
        return zones
    except Exception as e:
        print(f"Error fetching zones.json: {e}")
        return None

def load_games():
    """Load current games.json"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    if not games_file.exists():
        print("games.json not found")
        return None
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    return games

def extract_zone_id_from_imagepath(imagepath):
    """Extract zone ID from imagePath like https://cdn.jsdelivr.net/gh/gn-math/covers@main/42.png"""
    if not imagepath:
        return None
    match = re.search(r'/(\d+)\.png$', imagepath)
    if match:
        return int(match.group(1))
    return None

def match_games(games, zones):
    """Match games with zones and update names/imagePath"""
    # Create lookup dictionaries
    zones_by_id = {}
    zones_by_name_lower = {}
    
    for zone in zones:
        if isinstance(zone, dict) and 'id' in zone and zone['id'] != -1:
            zone_id = zone['id']
            zones_by_id[zone_id] = zone
            if 'name' in zone:
                zones_by_name_lower[zone['name'].lower()] = zone
    
    print(f"\nMatching games...")
    print("=" * 60)
    
    updated_count = 0
    matched_count = 0
    non_semag_games = [g for g in games if g.get('source') == 'non-semag']
    print(f"Found {len(non_semag_games)} non-semag games to check\n")
    
    for game in non_semag_games:
        game_name = game.get('name', '')
        game_dir = game.get('directory', '')
        imagepath = game.get('imagePath', '')
        
        # Try to extract zone ID from imagePath
        zone_id = extract_zone_id_from_imagepath(imagepath)
        matched_zone = None
        
        if zone_id is not None and zone_id in zones_by_id:
            # Match by zone ID from imagePath
            matched_zone = zones_by_id[zone_id]
        elif game_name.lower() in zones_by_name_lower:
            # Match by name
            matched_zone = zones_by_name_lower[game_name.lower()]
        
        if matched_zone:
            matched_count += 1
            correct_name = matched_zone.get('name', game_name)
            correct_id = matched_zone.get('id')
            correct_imagepath = f"{COVERS_BASE}{correct_id}.png"
            correct_directory = slugify(correct_name)
            
            # Check if anything needs updating
            needs_update = False
            updates = []
            
            if game.get('name') != correct_name:
                game['name'] = correct_name
                updates.append(f"name: '{game.get('name')}' -> '{correct_name}'")
                needs_update = True
            
            if game.get('imagePath') != correct_imagepath:
                game['imagePath'] = correct_imagepath
                updates.append(f"imagePath: updated to zone {correct_id}")
                needs_update = True
            
            if game.get('directory') != correct_directory:
                old_dir = game.get('directory')
                game['directory'] = correct_directory
                updates.append(f"directory: '{old_dir}' -> '{correct_directory}'")
                needs_update = True
            
            # Update author if available
            if 'author' in matched_zone:
                correct_author = matched_zone.get('author', '')
                if game.get('author') != correct_author:
                    game['author'] = correct_author
                    updates.append(f"author: '{game.get('author', '')}' -> '{correct_author}'")
                    needs_update = True
            
            # Update authorLink if available
            if 'authorLink' in matched_zone:
                correct_author_link = matched_zone.get('authorLink', '')
                if game.get('authorLink') != correct_author_link:
                    game['authorLink'] = correct_author_link
                    updates.append(f"authorLink: updated")
                    needs_update = True
            
            # Update image field (cover.png) if it exists
            if game.get('image') and game.get('image') != 'cover.png':
                game['image'] = 'cover.png'
                updates.append(f"image: updated to 'cover.png'")
                needs_update = True
            
            if needs_update:
                updated_count += 1
                print(f"  [{matched_count}] Updated: {game_name}")
                for update in updates:
                    print(f"      - {update}")
            else:
                # Still count as matched even if no updates needed
                if matched_count % 50 == 0:
                    print(f"  [{matched_count}] Already up-to-date: {game_name}")
        else:
            # Try to find by directory name or partial name match
            if imagepath and '/gn-math/covers@main/' in imagepath:
                print(f"  [?] Could not match: {game_name} (dir: {game_dir})")
    
    print("\n" + "=" * 60)
    print(f"Matched: {matched_count}/{len(non_semag_games)} games")
    print(f"Updated: {updated_count} games")
    
    return games

def main():
    print("GN-Math Game Matcher")
    print("=" * 60)
    
    # Load zones
    zones = load_zones()
    if not zones:
        return
    
    # Load games
    games = load_games()
    if not games:
        return
    
    print(f"Current games in database: {len(games)}")
    
    # Match and update
    updated_games = match_games(games, zones)
    
    # Save updated games.json
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(updated_games, f, indent='\t', ensure_ascii=False)
    
    print(f"\n✓ Saved updated games.json")
    print(f"✓ Total games: {len(updated_games)}")

if __name__ == "__main__":
    main()

