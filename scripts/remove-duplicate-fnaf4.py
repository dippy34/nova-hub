#!/usr/bin/env python3
"""
Remove duplicate FNAF 4 entries (keep one zone 42, remove the other)
"""
import json
from pathlib import Path

def main():
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    print("Loading games...", flush=True)
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print(f"Total games: {len(games)}", flush=True)
    
    # Find all FNAF 4 entries with zone 42
    zone42_entries = []
    for i, game in enumerate(games):
        if game.get('imagePath') == 'https://cdn.jsdelivr.net/gh/gn-math/covers@main/42.png':
            zone42_entries.append((i, game))
    
    print(f"\nFound {len(zone42_entries)} FNAF 4 entries from zone 42", flush=True)
    
    if len(zone42_entries) > 1:
        # Keep the first one, remove the rest
        games_to_keep = []
        removed = 0
        for i, game in enumerate(games):
            if game.get('imagePath') == 'https://cdn.jsdelivr.net/gh/gn-math/covers@main/42.png':
                if removed == 0:
                    # Keep the first one
                    print(f"Keeping FNAF 4 at index {i}: {game.get('name')}", flush=True)
                    games_to_keep.append(game)
                    removed += 1
                else:
                    # Remove duplicates
                    print(f"Removing duplicate FNAF 4 at index {i}: {game.get('name')}", flush=True)
                    removed += 1
            else:
                games_to_keep.append(game)
        
        # Save updated games
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(games_to_keep, f, indent='\t', ensure_ascii=False)
        
        print(f"\n✓ Removed {removed - 1} duplicate(s)", flush=True)
        print(f"✓ Total games: {len(games_to_keep)}", flush=True)
    else:
        print("No duplicates to remove", flush=True)

if __name__ == "__main__":
    main()


