#!/usr/bin/env python3
"""
Check which games use iframes to load external content
"""
import json
import os
import re
from pathlib import Path

GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
NON_SEMAG_DIR = Path(__file__).parent.parent / "non-semag"

def main():
    # Load games.json
    with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    games = data if isinstance(data, list) else data.get('games', [])
    
    print("Checking for iframed games...")
    print("=" * 60, flush=True)
    
    iframe_games = []
    external_iframe_games = []
    
    # Check games.json for external URLs
    for game in games:
        url = game.get('url', '')
        if url and 'http' in url and 'non-semag' not in url and 'semag' not in url:
            external_iframe_games.append({
                'name': game.get('name', 'Unknown'),
                'url': url,
                'directory': game.get('directory', 'N/A')
            })
    
    # Check HTML files for iframes with external src
    for root, dirs, files in os.walk(NON_SEMAG_DIR):
        if 'index.html' in files:
            html_path = Path(root) / 'index.html'
            try:
                with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Look for iframes with external URLs
                    iframe_pattern = r'<iframe[^>]*src\s*=\s*["\']([^"\']+)["\']'
                    matches = re.findall(iframe_pattern, content, re.I)
                    
                    for match in matches:
                        if match and (match.startswith('http://') or match.startswith('https://')):
                            game_name = os.path.basename(root)
                            iframe_games.append({
                                'name': game_name,
                                'iframe_src': match,
                                'path': str(html_path.relative_to(NON_SEMAG_DIR.parent))
                            })
            except Exception as e:
                pass
    
    print(f"\nGames with external URLs in games.json: {len(external_iframe_games)}", flush=True)
    if external_iframe_games:
        for game in external_iframe_games[:10]:
            print(f"  - {game['name']}: {game['url']}", flush=True)
    
    print(f"\nGames with iframes loading external content: {len(iframe_games)}", flush=True)
    if iframe_games:
        for game in iframe_games[:10]:
            print(f"  - {game['name']}: {game['iframe_src']}", flush=True)
    
    total_iframed = len(external_iframe_games) + len(iframe_games)
    print(f"\n{'=' * 60}", flush=True)
    print(f"Total iframed games: {total_iframed}", flush=True)

if __name__ == "__main__":
    main()


