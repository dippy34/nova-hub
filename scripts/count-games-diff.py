#!/usr/bin/env python3
"""Count games difference between local and remote"""
import json
import subprocess
from pathlib import Path

# Get local count
games_file = Path(__file__).parent.parent / "data" / "games.json"
with open(games_file, 'r', encoding='utf-8') as f:
    local_games = json.load(f)

local_count = len(local_games)
print(f"Local games: {local_count}")

# Try to get remote count
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
        remote_count = len(remote_games)
        print(f"Remote games: {remote_count}")
        print(f"\nAhead by: {local_count - remote_count} games")
    else:
        print("Could not fetch remote games.json")
except Exception as e:
    print(f"Error: {e}")
    # Fallback: estimate from git diff
    print("\nEstimating from git diff...")
    result = subprocess.run(
        ['git', 'diff', 'origin/main', '--stat', 'data/games.json'],
        capture_output=True,
        text=True
    )
    print(result.stdout)



