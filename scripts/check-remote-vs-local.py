#!/usr/bin/env python3
"""Check what games are in remote but not in local"""
import json
import subprocess
from pathlib import Path

# Get local games
games_file = Path(__file__).parent.parent / "data" / "games.json"
with open(games_file, 'r', encoding='utf-8') as f:
    local_games = json.load(f)

local_dirs = {g.get('directory', '') for g in local_games}
local_names = {g.get('name', '').lower() for g in local_games}

# Get remote games
try:
    result = subprocess.run(
        ['git', 'show', 'origin/main:data/games.json'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    if result.returncode == 0:
        remote_games = json.loads(result.stdout)
        
        # Find games in remote but not in local
        missing_games = []
        for game in remote_games:
            name = game.get('name', '')
            directory = game.get('directory', '')
            
            if name.lower() not in local_names and directory not in local_dirs:
                missing_games.append(game)
        
        if missing_games:
            print(f"Games in remote but NOT in local ({len(missing_games)}):")
            print("=" * 60)
            for game in missing_games:
                print(f"  - {game.get('name')} ({game.get('directory')})")
        else:
            print("All remote games are also in local database.")
    else:
        print("Could not fetch remote games.json")
except Exception as e:
    print(f"Error: {e}")


