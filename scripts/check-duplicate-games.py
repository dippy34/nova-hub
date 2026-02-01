#!/usr/bin/env python3
"""
Check for duplicate games in the database
"""
import json
from pathlib import Path
from collections import defaultdict

def normalize_name(name):
    """Normalize game name for comparison"""
    if not name:
        return ""
    return name.lower().strip()

def main():
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    if not games_file.exists():
        print("games.json not found!")
        return
    
    print("Loading games...", flush=True)
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print(f"Total games in database: {len(games)}")
    print("=" * 60, flush=True)
    
    # Check for duplicates by name
    name_groups = defaultdict(list)
    for i, game in enumerate(games):
        name = normalize_name(game.get('name', ''))
        if name:
            name_groups[name].append((i, game))
    
    name_duplicates = {name: games_list for name, games_list in name_groups.items() if len(games_list) > 1}
    
    # Check for duplicates by directory
    dir_groups = defaultdict(list)
    for i, game in enumerate(games):
        directory = game.get('directory', '').lower().strip()
        if directory:
            dir_groups[directory].append((i, game))
    
    dir_duplicates = {dir_name: games_list for dir_name, games_list in dir_groups.items() if len(games_list) > 1}
    
    # Check for duplicates by imagePath (same cover image)
    image_groups = defaultdict(list)
    for i, game in enumerate(games):
        image_path = game.get('imagePath', '').strip()
        if image_path:
            image_groups[image_path].append((i, game))
    
    image_duplicates = {img_path: games_list for img_path, games_list in image_groups.items() if len(games_list) > 1}
    
    # Report results
    print("\nDUPLICATE CHECK RESULTS")
    print("=" * 60, flush=True)
    
    if name_duplicates:
        print(f"\n⚠ Found {len(name_duplicates)} duplicate names:", flush=True)
        for name, games_list in sorted(name_duplicates.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n  Name: '{name}' ({len(games_list)} occurrences)", flush=True)
            for idx, game in games_list:
                dir_name = game.get('directory', 'N/A')
                source = game.get('source', 'N/A')
                print(f"    - Index {idx}: directory='{dir_name}', source='{source}'", flush=True)
    else:
        print("\n✓ No duplicate names found", flush=True)
    
    if dir_duplicates:
        print(f"\n⚠ Found {len(dir_duplicates)} duplicate directories:", flush=True)
        for dir_name, games_list in sorted(dir_duplicates.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n  Directory: '{dir_name}' ({len(games_list)} occurrences)", flush=True)
            for idx, game in games_list:
                name = game.get('name', 'N/A')
                source = game.get('source', 'N/A')
                print(f"    - Index {idx}: name='{name}', source='{source}'", flush=True)
    else:
        print("\n✓ No duplicate directories found", flush=True)
    
    if image_duplicates:
        print(f"\n⚠ Found {len(image_duplicates)} duplicate image paths:", flush=True)
        for img_path, games_list in sorted(image_duplicates.items(), key=lambda x: len(x[1]), reverse=True):
            if len(games_list) > 1:
                print(f"\n  Image: '{img_path}' ({len(games_list)} occurrences)", flush=True)
                for idx, game in games_list:
                    name = game.get('name', 'N/A')
                    dir_name = game.get('directory', 'N/A')
                    print(f"    - Index {idx}: name='{name}', directory='{dir_name}'", flush=True)
    else:
        print("\n✓ No duplicate image paths found", flush=True)
    
    # Summary
    print("\n" + "=" * 60, flush=True)
    print("SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"Total games: {len(games)}", flush=True)
    print(f"Duplicate names: {len(name_duplicates)}", flush=True)
    print(f"Duplicate directories: {len(dir_duplicates)}", flush=True)
    print(f"Duplicate image paths: {len(image_duplicates)}", flush=True)
    
    if name_duplicates or dir_duplicates or image_duplicates:
        total_duplicate_entries = sum(len(games_list) - 1 for games_list in name_duplicates.values())
        total_duplicate_entries += sum(len(games_list) - 1 for games_list in dir_duplicates.values())
        print(f"\n⚠ Total duplicate entries found: {total_duplicate_entries}", flush=True)
    else:
        print("\n✓ No duplicates found! Database is clean.", flush=True)

if __name__ == "__main__":
    main()

