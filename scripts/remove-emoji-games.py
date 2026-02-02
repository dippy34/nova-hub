#!/usr/bin/env python3
"""Remove games with emojis or 'play on crazygames' from games.json"""
import json
import re
from pathlib import Path

GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"

def main():
    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    games = data if isinstance(data, list) else data.get('games', [])
    
    # Find games to remove
    games_to_remove = []
    for game in games:
        name = game.get('name', '')
        # Check for emojis or "play on crazygames"
        if re.search(r'[🕹️🎮🎯🎲🎨🎪🎭🎬🎤🎧🎵🎶🎸🎺🎻🥁🎹🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿]', name) or 'play on crazygames' in name.lower():
            games_to_remove.append(game)
    
    print(f"Found {len(games_to_remove)} games to remove:", flush=True)
    for game in games_to_remove:
        print(f"  - {game.get('name')} ({game.get('directory')})", flush=True)
    
    # Remove them
    games = [g for g in games if g not in games_to_remove]
    
    if isinstance(data, dict):
        data['games'] = games
    else:
        data = games
    
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent='\t', ensure_ascii=False)
    
    print(f"\nRemoved {len(games_to_remove)} games", flush=True)

if __name__ == "__main__":
    main()

