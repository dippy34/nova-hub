#!/usr/bin/env python3
"""
Download actual game files from Escape Road iframe sources
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import os
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"

def download_file(url, filepath, silent=False):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=15)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        if not silent:
            print(f"    Error downloading {url}: {e}", flush=True)
        return False

def download_game_from_url(game_name, game_dir, iframe_url):
    """Download game files from iframe URL"""
    print(f"  Downloading from: {iframe_url}", flush=True)
    
    try:
        # Fetch the game page
        r = requests.get(iframe_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Get the base URL for relative links
        parsed_url = urlparse(iframe_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Find all script and link tags that need to be downloaded
        assets_to_download = []
        
        # Scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if src:
                full_url = urljoin(iframe_url, src)
                assets_to_download.append(('script', src, full_url))
        
        # Stylesheets
        for link in soup.find_all('link', rel='stylesheet', href=True):
            href = link.get('href', '')
            if href:
                full_url = urljoin(iframe_url, href)
                assets_to_download.append(('stylesheet', href, full_url))
        
        # Images
        for img in soup.find_all('img', src=True):
            src = img.get('src', '')
            if src and not src.startswith('data:'):
                full_url = urljoin(iframe_url, src)
                assets_to_download.append(('image', src, full_url))
        
        # Download assets
        assets_dir = game_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        downloaded_assets = {}
        for asset_type, relative_path, full_url in assets_to_download:
            # Skip external CDNs (like jsdelivr, cdnjs, etc.)
            if any(cdn in full_url for cdn in ['cdn.jsdelivr.net', 'cdnjs.cloudflare.com', 'unpkg.com', 'cdnjs.com', 'gstatic.com', 'googletagmanager.com']):
                continue
            
            # Skip data URLs
            if relative_path.startswith('data:'):
                continue
            
            # Create local path - handle both relative and absolute URLs
            if relative_path.startswith('http://') or relative_path.startswith('https://'):
                # Full URL - extract path and sanitize
                parsed = urlparse(relative_path)
                # Use domain and path, sanitize for filesystem
                safe_path = parsed.netloc.replace(':', '_') + parsed.path.replace('/', '_').replace('\\', '_')
                local_path = assets_dir / safe_path
            elif relative_path.startswith('/'):
                # Absolute path from root
                local_path = assets_dir / relative_path.lstrip('/').replace('/', '_')
            else:
                # Relative path - sanitize
                local_path = assets_dir / relative_path.replace('/', '_').replace('\\', '_')
            
            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            if download_file(full_url, local_path, silent=True):
                # Update the HTML to point to local asset
                relative_local = f"assets/{local_path.name}"
                downloaded_assets[relative_path] = relative_local
        
        # Update HTML to use local assets
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if src in downloaded_assets:
                script['src'] = downloaded_assets[src]
        
        for link in soup.find_all('link', rel='stylesheet', href=True):
            href = link.get('href', '')
            if href in downloaded_assets:
                link['href'] = downloaded_assets[href]
        
        for img in soup.find_all('img', src=True):
            src = img.get('src', '')
            if src in downloaded_assets:
                img['src'] = downloaded_assets[src]
        
        # Save the updated HTML
        html_file = game_dir / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"    ✓ Downloaded {len(downloaded_assets)} assets", flush=True)
        return True
        
    except Exception as e:
        print(f"    ✗ Error: {e}", flush=True)
        return False

def main():
    print("Escape Road Games Local Downloader")
    print("=" * 60, flush=True)
    
    escape_games = [
        'escape-road',
        'escape-road-2',
        'escape-road-city',
        'escape-road-city-2',
        'escape-road-winter',
        'escape-road-halloween'
    ]
    
    # Map of game directories to their iframe URLs
    iframe_urls = {
        'escape-road': 'https://azgames.io/game/escape-road/',
        'escape-road-2': 'https://game.azgame.io/escape-road-2/',
        'escape-road-city': 'https://game.azgame.io/escape-road-city/',
        'escape-road-city-2': 'https://game.azgame.io/escape-road-city-2/',
        'escape-road-winter': 'https://azgames.io/game/escape-road-winter.embed',
        'escape-road-halloween': 'https://azgames.io/escape-road-halloween.embed',
    }
    
    # Fix .embed URLs - they might need to be converted to regular URLs
    for key, url in iframe_urls.items():
        if url.endswith('.embed'):
            # Try without .embed
            test_url = url.replace('.embed', '/')
            try:
                r = requests.head(test_url, headers=HEADERS, timeout=5, allow_redirects=True)
                if r.status_code == 200:
                    iframe_urls[key] = test_url
            except:
                pass
    
    downloaded_count = 0
    failed_count = 0
    
    for i, game_dir_name in enumerate(escape_games, 1):
        game_dir = GAMES_DIR / game_dir_name
        iframe_url = iframe_urls.get(game_dir_name)
        
        if not iframe_url:
            print(f"[{i}/{len(escape_games)}] ⚠ No URL found for {game_dir_name}", flush=True)
            continue
        
        print(f"\n[{i}/{len(escape_games)}] Processing: {game_dir_name}", flush=True)
        
        if download_game_from_url(game_dir_name, game_dir, iframe_url):
            downloaded_count += 1
            print(f"  ✓ Success: {game_dir_name}", flush=True)
        else:
            failed_count += 1
            print(f"  ✗ Failed: {game_dir_name}", flush=True)
        
        time.sleep(1)  # Be polite
    
    print(f"\n" + "=" * 60, flush=True)
    print(f"DOWNLOAD SUMMARY", flush=True)
    print(f"=" * 60, flush=True)
    print(f"Successfully downloaded: {downloaded_count}/{len(escape_games)}", flush=True)
    print(f"Failed: {failed_count}/{len(escape_games)}", flush=True)

if __name__ == "__main__":
    main()

