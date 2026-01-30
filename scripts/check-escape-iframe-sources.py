#!/usr/bin/env python3
"""Check iframe sources for Escape Road games"""
from pathlib import Path
from bs4 import BeautifulSoup

games_dir = Path(__file__).parent.parent / "non-semag"
escape_games = ['escape-road', 'escape-road-2', 'escape-road-city', 'escape-road-city-2', 'escape-road-winter', 'escape-road-halloween']

print("Iframe sources:")
for game in escape_games:
    html_file = games_dir / game / "index.html"
    if html_file.exists():
        soup = BeautifulSoup(html_file.read_text(encoding='utf-8'), 'html.parser')
        iframe = soup.find('iframe')
        if iframe:
            src = iframe.get('src', '')
            print(f"  {game}: {src}")

