#!/usr/bin/env python3
"""
Remove all Minecraft games except Minecraft Indev
"""
import json
from pathlib import Path

def main():
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    print("Loading games...", flush=True)
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print(f"Total games: {len(games)}", flush=True)
    
    # Find and remove Minecraft games except Indev
    games_to_keep = []
    removed = []
    
    for game in games:
        name = game.get('name', '').lower()
        directory = game.get('directory', '').lower()
        
        # Check if it's a Minecraft game
        is_minecraft = 'minecraft' in name or 'minecraft' in directory
        
        if is_minecraft:
            # Check if it's Minecraft Indev (keep this one)
            if 'indev' in name.lower() or 'indev' in directory:
                print(f"Keeping: {game.get('name', 'Unknown')}", flush=True)
                games_to_keep.append(game)
            else:
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
    print(f"Removed: {len(removed)} Minecraft games", flush=True)
    for name in removed:
        print(f"  - {name}", flush=True)
    print(f"\nKept: Minecraft Indev", flush=True)
    print(f"Total games: {len(games_to_keep)}", flush=True)
    print(f"✓ Saved updated games.json", flush=True)

if __name__ == "__main__":
    main()


