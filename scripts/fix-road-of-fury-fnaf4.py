#!/usr/bin/env python3
"""
Fix the Road of Fury entries - zone 42 is actually FNAF 4, not Road of Fury
"""
import json
from pathlib import Path

def main():
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    print("Loading games...", flush=True)
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print(f"Total games: {len(games)}", flush=True)
    
    # Find and fix Road of Fury entries (zone 42)
    fixed_count = 0
    removed_count = 0
    
    # Check if we already have FNAF 4 from zone 41
    has_fnaf4_zone41 = False
    for game in games:
        if game.get('imagePath') == 'https://cdn.jsdelivr.net/gh/gn-math/covers@main/41.png':
            has_fnaf4_zone41 = True
            print(f"Found existing FNAF 4 (zone 41): {game.get('name')}", flush=True)
            break
    
    # Process games
    games_to_keep = []
    for i, game in enumerate(games):
        imagepath = game.get('imagePath', '')
        
        # Check if this is zone 42 (Road of Fury mislabeled)
        if imagepath == 'https://cdn.jsdelivr.net/gh/gn-math/covers@main/42.png':
            # This is actually FNAF 4, not Road of Fury
            if has_fnaf4_zone41:
                # We already have FNAF 4 from zone 41, so remove this duplicate
                print(f"Removing duplicate FNAF 4 (zone 42) at index {i}: {game.get('name')}", flush=True)
                removed_count += 1
                continue
            else:
                # Update it to be FNAF 4
                print(f"Fixing zone 42 at index {i}: '{game.get('name')}' -> 'Five Nights at Freddy's 4'", flush=True)
                game['name'] = "Five Nights at Freddy's 4"
                game['directory'] = "five-nights-at-freddys-4"
                game['author'] = "Scott Cawthon"
                game['authorLink'] = "https://scottgames.com"
                fixed_count += 1
                games_to_keep.append(game)
        else:
            games_to_keep.append(game)
    
    # Save updated games
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games_to_keep, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("FIX SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"Fixed: {fixed_count} games", flush=True)
    print(f"Removed: {removed_count} duplicates", flush=True)
    print(f"Total games: {len(games_to_keep)}", flush=True)
    print(f"\n✓ Saved updated games.json", flush=True)

if __name__ == "__main__":
    main()


