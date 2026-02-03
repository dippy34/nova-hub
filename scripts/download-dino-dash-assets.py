#!/usr/bin/env python3
"""
Download missing assets for Dino Dash game
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

GAME_URL = "https://lagged.com/en/g/dino-dash"
BASE_DIR = Path(__file__).parent.parent / "non-semag" / "dino-dash"
ASSETS_DIR = BASE_DIR / "assets"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://lagged.com/'
}

def download_file(url, dest_path):
    """Download a file from URL to destination path"""
    try:
        print(f"Downloading: {url}")
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"  ✓ Saved to {dest_path}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def find_play_url():
    """Find the actual game play URL"""
    print(f"Fetching game page: {GAME_URL}")
    r = requests.get(GAME_URL, headers=HEADERS)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Look for iframe
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        play_url = iframe.get('src')
        if not play_url.startswith('http'):
            play_url = urljoin(GAME_URL, play_url)
        print(f"Found iframe URL: {play_url}")
        return play_url
    
    # Look for script tags with game URLs
    scripts = soup.find_all('script')
    for script in scripts:
        src = script.get('src', '')
        if 'dino-dash' in src.lower():
            play_url = urljoin(GAME_URL, src)
            print(f"Found script URL: {play_url}")
            return play_url
    
    return None

def download_game_assets(play_url):
    """Download all assets from the game page"""
    print(f"\nFetching game page: {play_url}")
    r = requests.get(play_url, headers=HEADERS)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    base_url = '/'.join(play_url.split('/')[:-1]) + '/'
    
    # Find all asset references
    assets = set()
    
    # Look for assetData.json references
    text = r.text
    asset_data_matches = re.findall(r'["\']([^"\']*assetData\.json[^"\']*)["\']', text, re.IGNORECASE)
    for match in asset_data_matches:
        if not match.startswith('http'):
            match = urljoin(base_url, match)
        assets.add(match)
    
    # Look for script tags
    scripts = soup.find_all('script')
    for script in scripts:
        src = script.get('src', '')
        if src:
            if not src.startswith('http'):
                src = urljoin(base_url, src)
            assets.add(src)
    
    # Look for link tags (CSS, etc.)
    links = soup.find_all('link')
    for link in links:
        href = link.get('href', '')
        if href:
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            assets.add(href)
    
    # Find asset references in JavaScript
    js_assets = re.findall(r'["\']([^"\']*\.(json|wasm|data|br|png|jpg|jpeg|gif|webp|ttf|woff|woff2)[^"\']*)["\']', text, re.IGNORECASE)
    for match in js_assets:
        asset_url = match[0]
        if not asset_url.startswith('http') and not asset_url.startswith('data:'):
            asset_url = urljoin(base_url, asset_url)
            assets.add(asset_url)
    
    print(f"\nFound {len(assets)} asset references")
    
    # Download assets
    downloaded = 0
    for asset_url in assets:
        if 'assetData.json' in asset_url.lower():
            # Download to assets directory
            dest = ASSETS_DIR / "assetData.json"
            if download_file(asset_url, dest):
                downloaded += 1
        elif asset_url.endswith('.json'):
            # Download JSON files to assets directory
            filename = os.path.basename(urlparse(asset_url).path)
            dest = ASSETS_DIR / filename
            if download_file(asset_url, dest):
                downloaded += 1
        elif asset_url.endswith(('.wasm', '.data', '.br')):
            # Download binary files to assets directory
            filename = os.path.basename(urlparse(asset_url).path)
            dest = ASSETS_DIR / filename
            if download_file(asset_url, dest):
                downloaded += 1
    
    print(f"\n✓ Downloaded {downloaded} assets")
    return downloaded

def main():
    print("Dino Dash Asset Downloader")
    print("=" * 50)
    
    # Create assets directory
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find play URL
    play_url = find_play_url()
    if not play_url:
        print("✗ Could not find game play URL")
        return
    
    # Download assets
    download_game_assets(play_url)
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()



