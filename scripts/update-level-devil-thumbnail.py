#!/usr/bin/env python3
import json
from pathlib import Path
import requests

games_path = Path("data/games.json")
games = json.load(open(games_path, 'r', encoding='utf-8'))

games_list = games if isinstance(games, list) else games.get('games', [])

game = next((g for g in games_list if g.get('directory') == 'level-devil'), None)
if game:
    game['image'] = 'splash.avif'
    print(f"Updated thumbnail to: {game['image']}")

games_data = games if isinstance(games, list) else {'games': games_list}
json.dump(games_data, open(games_path, 'w', encoding='utf-8'), indent='\t', ensure_ascii=False)

# Check if splash.avif exists, if not try to download it
game_dir = Path("non-semag/level-devil")
splash_path = game_dir / "splash.avif"

if not splash_path.exists():
    print("\nDownloading splash.avif...")
    splash_url = "https://d3rtzzzsiu7gdr.cloudfront.net/play/splash.avif"
    try:
        r = requests.get(splash_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        r.raise_for_status()
        with open(splash_path, 'wb') as f:
            f.write(r.content)
        print(f"  ✓ Downloaded splash.avif")
    except Exception as e:
        print(f"  ✗ Failed to download splash.avif: {e}")
else:
    print(f"\n✓ splash.avif already exists")

