#!/usr/bin/env python3
"""
Fix Dino Dash assets by finding and downloading assetData.json
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Referer': 'https://lagged.com/'
}

BASE_DIR = Path(__file__).parent.parent / "non-semag" / "dino-dash"
ASSETS_DIR = BASE_DIR / "assets"

def find_asset_urls():
    """Try to find asset URLs from common PlayCanvas CDN patterns"""
    # Common PlayCanvas CDN patterns
    possible_urls = [
        "https://contentstorage.online.tech/playcanvas/",
        "https://playcanv.as/",
        "https://launch.playcanvas.com/",
    ]
    
    # Try to find from the JS file
    js_file = BASE_DIR / "js" / "index-BVfBOMvs.js"
    if js_file.exists():
        with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Look for URLs in the JS
            urls = re.findall(r'https?://[^\s"\'<>]+', content)
            for url in urls:
                if 'asset' in url.lower() or 'playcanvas' in url.lower():
                    print(f"Found potential asset URL in JS: {url[:200]}")
    
    # Try common asset paths based on game name
    base_paths = [
        "https://lagged.com/games/dino-dash-v2/",
        "https://imgs2.dab3games.com/dino-dash/",
    ]
    
    return base_paths

def try_download_asset(url, filename="assetData.json"):
    """Try to download an asset from a URL"""
    try:
        # Try the direct URL
        test_url = urljoin(url, filename)
        print(f"Trying: {test_url}")
        r = requests.get(test_url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            dest = ASSETS_DIR / filename
            ASSETS_DIR.mkdir(parents=True, exist_ok=True)
            with open(dest, 'wb') as f:
                f.write(r.content)
            print(f"  ✓ Downloaded {filename}")
            return True
    except Exception as e:
        pass
    
    return False

def create_minimal_asset_data():
    """Create a minimal assetData.json if we can't download it"""
    minimal_data = {
        "assets": [],
        "scripts": [],
        "scenes": []
    }
    
    dest = ASSETS_DIR / "assetData.json"
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(dest, 'w') as f:
        json.dump(minimal_data, f, indent=2)
    
    print(f"Created minimal assetData.json at {dest}")
    return True

def main():
    print("Dino Dash Asset Fixer")
    print("=" * 50)
    
    # Try to find and download assets
    base_paths = find_asset_urls()
    
    downloaded = False
    for base_path in base_paths:
        if try_download_asset(base_path, "assetData.json"):
            downloaded = True
            break
    
    if not downloaded:
        print("\nCould not download assetData.json from known sources")
        print("Creating minimal assetData.json...")
        create_minimal_asset_data()
        print("\n⚠ Note: The game may not work fully without the complete asset data.")
        print("   You may need to manually download assets from the original game page.")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()


