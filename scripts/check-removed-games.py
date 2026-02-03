#!/usr/bin/env python3
"""Check what games were actually removed"""
import json
import subprocess
from pathlib import Path

# Get current games
games_file = Path(__file__).parent.parent / "data" / "games.json"
with open(games_file, 'r', encoding='utf-8') as f:
    current_games = json.load(f)

# Get previous commit games
result = subprocess.run(
    ['git', 'show', 'HEAD:data/games.json'],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

if result.returncode == 0:
    old_games = json.loads(result.stdout)
    
    # Find Escape Road games in old database
    old_escape = {g.get('name'): g for g in old_games if 'escape' in g.get('name', '').lower()}
    
    # Find Escape Road games in current database
    current_escape = {g.get('name'): g for g in current_games if 'escape' in g.get('name', '').lower()}
    
    print("Games that were REMOVED:")
    for name in old_escape:
        if name not in current_escape:
            game = old_escape[name]
            print(f"  - {name} (directory: {game.get('directory')})")
    
    print(f"\nTotal removed: {len(old_escape) - len(set(old_escape.keys()) & set(current_escape.keys()))}")
else:
    print("Could not access previous commit")


