#!/usr/bin/env python3
"""Update Obby Tsunami cover image"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path

game_dir = Path(__file__).parent.parent / "non-semag" / "obby-tsunami-1-speed-play-online-for-free-on-playhop"
url = "https://playhop.com/app/477210"

print("Fetching playhop page...")
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
r.raise_for_status()

soup = BeautifulSoup(r.text, 'html.parser')

# Try to find the actual game thumbnail
cover_url = None

# Try og:image
og_image = soup.find('meta', property='og:image')
if og_image:
    cover_url = og_image.get('content')
    print(f"Found og:image: {cover_url}")

# If it's a playhop URL, try to find the actual game image
if cover_url and 'playhop' in cover_url.lower():
    # Look for game image in JSON-LD or other metadata
    json_ld = soup.find('script', type='application/ld+json')
    if json_ld:
        import json
        try:
            data = json.loads(json_ld.string)
            if isinstance(data, dict) and 'image' in data:
                cover_url = data['image']
                print(f"Found JSON-LD image: {cover_url}")
        except:
            pass

# Try to get from Yandex Games directly
if not cover_url or 'playhop' in cover_url.lower():
    # Try common Yandex Games thumbnail paths
    base_url = "https://app-477210.games.s3.yandex.net/477210/mfdcsrqpc7fbyzatazyovu9d4xkvq8hf_brotli"
    possible_paths = [
        "/TemplateData/logo.png",
        "/logo.png",
        "/cover.png",
        "/icon.png"
    ]
    
    for path in possible_paths:
        test_url = base_url + path
        try:
            test_r = requests.head(test_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if test_r.status_code == 200:
                cover_url = test_url
                print(f"Found Yandex image: {cover_url}")
                break
        except:
            continue

if cover_url:
    print(f"\nDownloading cover from: {cover_url}")
    r2 = requests.get(cover_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
    r2.raise_for_status()
    
    with open(game_dir / "cover.png", 'wb') as f:
        f.write(r2.content)
    
    print(f"✓ Downloaded cover image ({len(r2.content):,} bytes)")
else:
    print("✗ Could not find cover image URL")

