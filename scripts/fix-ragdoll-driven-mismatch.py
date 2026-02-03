#!/usr/bin/env python3
"""
Fix the Ragdoll Hit / Driven Wild mismatch
"""
import json
from pathlib import Path

def main():
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    print("Fixing Ragdoll Hit / Driven Wild mismatch...")
    
    # Find and fix entries
    for game in games:
        if game.get('source') != 'non-semag':
            continue
        
        # The ragdoll-hit directory actually contains Driven Wild (zone 43)
        if game.get('directory') == 'ragdoll-hit':
            print(f"  Fixing: ragdoll-hit directory -> Driven Wild (zone 43)")
            game['name'] = 'Driven Wild'
            game['imagePath'] = 'https://cdn.jsdelivr.net/gh/gn-math/covers@main/43.png'
            game['imagePath'] = 'https://cdn.jsdelivr.net/gh/gn-math/covers@main/43.png'
        
        # Remove duplicate Driven Wild if it exists (keep the one in ragdoll-hit)
        if game.get('directory') == 'driven-wild' and game.get('name') == 'Driven Wild':
            print(f"  Removing duplicate: driven-wild directory (keeping ragdoll-hit)")
            game['_remove'] = True
    
    # Remove duplicates
    games = [g for g in games if not g.get('_remove')]
    
    # Remove duplicate Road of Fury entries
    seen_road = set()
    for game in games:
        if game.get('name') == 'Road of Fury':
            key = game.get('directory', '')
            if key in seen_road:
                print(f"  Removing duplicate: Road of Fury ({key})")
                game['_remove'] = True
            else:
                seen_road.add(key)
    
    games = [g for g in games if not g.get('_remove')]
    
    # Save
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print(f"\n✓ Fixed mismatches")
    print(f"✓ Total games: {len(games)}")

if __name__ == "__main__":
    main()



