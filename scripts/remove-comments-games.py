#!/usr/bin/env python3
"""
Remove comment/suggestion entries from games.json
"""
import json
from pathlib import Path

def main():
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    print("Loading games...", flush=True)
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print(f"Total games: {len(games)}", flush=True)
    
    # Find and remove comment/suggestion entries
    games_to_keep = []
    removed = []
    
    for game in games:
        name = game.get('name', '').lower()
        directory = game.get('directory', '').lower()
        
        # Check if it's a comment/suggestion entry
        if (name.startswith('[!]') or 
            'comment' in name or 
            'suggest' in name or
            directory == 'comments' or
            'comment' in directory or
            'suggest' in directory):
            removed.append(game.get('name', 'Unknown'))
            print(f"Removing: {game.get('name', 'Unknown')}", flush=True)
        else:
            games_to_keep.append(game)
    
    # Save updated games
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games_to_keep, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("REMOVAL SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"Removed: {len(removed)} comment/suggestion entries", flush=True)
    for name in removed:
        print(f"  - {name}", flush=True)
    print(f"\nTotal games: {len(games_to_keep)}", flush=True)
    print(f"✓ Saved updated games.json", flush=True)

if __name__ == "__main__":
    main()


