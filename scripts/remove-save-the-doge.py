#!/usr/bin/env python3
"""Remove Save The Doge game from games.json"""
import json
from pathlib import Path

GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"

def main():
    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    games = data if isinstance(data, list) else data.get('games', [])
    
    # Remove Save The Doge
    games = [g for g in games if 'doge' not in g.get('name', '').lower() and 'save_the_doge' not in g.get('directory', '').lower()]
    
    if isinstance(data, dict):
        data['games'] = games
    else:
        data = games
    
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent='\t', ensure_ascii=False)
    
    print("Removed Save The Doge from games.json", flush=True)

if __name__ == "__main__":
    main()


