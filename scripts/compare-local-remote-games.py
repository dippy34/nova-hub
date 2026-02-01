#!/usr/bin/env python3
"""
Compare local vs remote games.json count
"""
import json
import subprocess
from pathlib import Path

GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"

def main():
    # Get local count
    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        local_data = json.load(f)
    local_games = local_data if isinstance(local_data, list) else local_data.get('games', [])
    local_count = len(local_games)
    
    print(f"Local games: {local_count}", flush=True)
    
    # Try to get remote count
    try:
        result = subprocess.run(
            ['git', 'show', 'origin/main:data/games.json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            remote_data = json.loads(result.stdout)
            remote_games = remote_data if isinstance(remote_data, list) else remote_data.get('games', [])
            remote_count = len(remote_games)
            
            print(f"Remote games: {remote_count}", flush=True)
            print(f"Difference: {local_count - remote_count} games ahead", flush=True)
        else:
            print("Could not fetch remote games.json", flush=True)
            print("Make sure you have fetched the latest remote: git fetch origin", flush=True)
    except Exception as e:
        print(f"Error fetching remote: {e}", flush=True)
        print("Make sure you have fetched the latest remote: git fetch origin", flush=True)

if __name__ == "__main__":
    main()

