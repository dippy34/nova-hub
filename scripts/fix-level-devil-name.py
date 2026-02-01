#!/usr/bin/env python3
import json
from pathlib import Path

games_path = Path("data/games.json")
games = json.load(open(games_path, 'r', encoding='utf-8'))

games_list = games if isinstance(games, list) else games.get('games', [])

game = next((g for g in games_list if g.get('directory') == 'level-devil'), None)
if game:
    game['name'] = 'Level Devil'
    print(f"Updated game name to: {game['name']}")

games_data = games if isinstance(games, list) else {'games': games_list}
json.dump(games_data, open(games_path, 'w', encoding='utf-8'), indent='\t', ensure_ascii=False)

