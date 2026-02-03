#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import json

url = 'https://www.crazygames.com/game/deadly-descent-bzs'
headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(r.text, 'html.parser')

# Look for script tags with game data
scripts = soup.find_all('script')
for script in scripts:
    if script.string:
        # Look for game embed URLs
        patterns = [
            r'["\']([^"\']*game[^"\']*\.html[^"\']*)["\']',
            r'["\']([^"\']*embed[^"\']*)["\']',
            r'src:\s*["\']([^"\']+)["\']',
            r'url:\s*["\']([^"\']+)["\']',
            r'gameUrl:\s*["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, script.string, re.I)
            for match in matches:
                if 'game' in match.lower() or 'embed' in match.lower() or 'deadly' in match.lower():
                    print(f"Found potential game URL: {match}")

# Look for data attributes
game_div = soup.find('div', {'id': 'game-iframe'}) or soup.find('div', class_=re.compile('game', re.I))
if game_div:
    data_src = game_div.get('data-src') or game_div.get('data-url')
    if data_src:
        print(f"Found data-src: {data_src}")

# Check for JSON data
json_scripts = soup.find_all('script', type='application/json')
for script in json_scripts:
    try:
        data = json.loads(script.string)
        print(f"JSON data: {json.dumps(data, indent=2)[:500]}")
    except:
        pass

# Look for iframe in the HTML
iframes = soup.find_all('iframe')
for iframe in iframes:
    src = iframe.get('src', '')
    if src:
        print(f"Iframe src: {src}")


