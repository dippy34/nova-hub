#!/usr/bin/env python3
"""
Scraper for Hypackel game assets from hypackel.github.io/fork/0/g/
(Original source d3rtzzzsiu7gdr.cloudfront.net is inaccessible - using GitHub Pages mirror)
"""
import json
import os
import re
import time
import ssl
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from html.parser import HTMLParser

# d3rtzzzsiu7gdr.cloudfront.net returns 404 - using hypackel.github.io (same Hypackel content)
BASE_URL = "https://hypackel.github.io/fork/0/g/"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "Hypackel"
GAMES_JSON_URL = "https://hypackel.github.io/fork/0/g/games.json"

# Sanitize directory name for filesystem
def sanitize_dir(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def get_opener():
    ctx = ssl.create_default_context()
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))

def download_file(opener, url, filepath):
    """Download a file from URL to filepath"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        with opener.open(req, timeout=60) as resp:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  ✗ Failed {url}: {e}")
        return False

class AssetExtractor(HTMLParser):
    """Extract asset URLs from HTML"""
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.assets = set()
        self.scripts = []
        
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            url = attrs['href'].strip()
            if url and not url.startswith('#') and not url.startswith('javascript:'):
                self.assets.add(urljoin(self.base_url, url))
        elif tag == 'img' and 'src' in attrs:
            self.assets.add(urljoin(self.base_url, attrs['src']))
        elif tag == 'script' and 'src' in attrs:
            self.assets.add(urljoin(self.base_url, attrs['src']))
        elif tag == 'link':
            href = attrs.get('href', '')
            if href and ('rel' not in attrs or 'stylesheet' in str(attrs.get('rel', '')).lower() or 'icon' in str(attrs.get('rel', '')).lower()):
                self.assets.add(urljoin(self.base_url, href))
        elif tag == 'meta' and attrs.get('content'):
            if 'url=' in str(attrs):
                pass  # og:image etc
        elif tag in ('source', 'video', 'audio') and 'src' in attrs:
            self.assets.add(urljoin(self.base_url, attrs['src']))
        elif tag == 'embed' and 'src' in attrs:
            self.assets.add(urljoin(self.base_url, attrs['src']))
        elif tag == 'object' and 'data' in attrs:
            self.assets.add(urljoin(self.base_url, attrs['data']))

def extract_assets_from_html(html_content, base_url):
    """Extract all asset URLs from HTML content"""
    parser = AssetExtractor(base_url)
    try:
        parser.feed(html_content)
        return parser.assets
    except Exception:
        return set()

def url_to_local_path(url, base_url, dirname):
    """Convert URL to local file path relative to game directory"""
    if not url.startswith(base_url):
        return None
    path = url[len(base_url):].lstrip('/')
    path = unquote(path).split('?')[0]
    # Strip directory prefix - path might be "slope/game/x" for game slope
    if path.startswith(dirname + '/'):
        return path[len(dirname)+1:]
    elif path.startswith(dirname):
        return path[len(dirname):].lstrip('/')
    return path

def scrape_game(opener, game_info, games_list):
    """Scrape a single game's assets"""
    url = game_info.get('url', '')
    name = game_info.get('name', '')
    image_src = game_info.get('imageSrc', '')
    
    # Determine game directory
    if url.startswith('/fork/0/g/') and url.endswith('/'):
        dirname = url.replace('/fork/0/g/', '').rstrip('/')
    elif url.startswith('./') and '/' in url:
        dirname = url.replace('./', '').rstrip('/').split('/')[0]
    elif url.endswith('/') and not url.startswith('http') and 'fork/game' not in url and 'projects' not in url:
        dirname = url.rstrip('/').split('/')[-1]
    else:
        return None  # Skip proxy/external games
    
    # Skip if image is external only (no local assets to scrape)
    if image_src.startswith('http') and not any(x in url for x in ['/fork/0/g/', './']):
        # Check if we have local url
        if url.startswith('http') or '/fork/game/?' in url:
            return None
    
    dirname = sanitize_dir(dirname)
    game_base = BASE_URL + dirname + '/'
    game_dir = OUTPUT_DIR / dirname
    game_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = set()
    
    # Download index.html
    index_url = game_base + 'index.html'
    index_path = game_dir / 'index.html'
    if download_file(opener, index_url, index_path):
        downloaded.add('index.html')
        with open(index_path, 'r', encoding='utf-8', errors='replace') as f:
            html = f.read()
        assets = extract_assets_from_html(html, game_base)
        for asset_url in assets:
            if not asset_url.startswith(BASE_URL):
                continue
            local_path = url_to_local_path(asset_url, BASE_URL, dirname)
            if local_path and not local_path.startswith('../'):
                fp = game_dir / local_path
                if fp.suffix or '?' not in asset_url:
                    if download_file(opener, asset_url, fp):
                        downloaded.add(local_path)
    else:
        # Try index.htm or default
        for alt in ['index.htm', '']:
            if alt:
                alt_url = game_base + alt
            else:
                alt_url = game_base
            if download_file(opener, alt_url, index_path):
                break
    
    # Determine cover image path for games.json and download
    cover_path = 'cover.png'
    if image_src.startswith('./'):
        # Relative to g/ - e.g. ./slope/game/splash.jpg
        rel_path = image_src.replace('./', '')
        img_url = urljoin(BASE_URL, image_src)
        if rel_path.startswith(dirname + '/'):
            local_rel = rel_path[len(dirname)+1:]  # path relative to game dir
            cover_path = local_rel
            img_path = game_dir / local_rel
        else:
            cover_path = Path(rel_path).name
            img_path = game_dir / rel_path
        if download_file(opener, img_url, img_path):
            downloaded.add(rel_path)
    elif not image_src.startswith('http'):
        # Local path like "tanuki-sunset.png"
        img_url = urljoin(game_base, image_src)
        img_path = game_dir / image_src
        if download_file(opener, img_url, img_path):
            cover_path = image_src
            downloaded.add(image_src)
    else:
        # External image - download to game dir
        cover_name = Path(urlparse(image_src).path).name or 'cover.png'
        if download_file(opener, image_src, game_dir / cover_name):
            cover_path = cover_name
    
    games_list.append({
        'name': name,
        'directory': dirname,
        'image': cover_path if isinstance(cover_path, str) else str(cover_path),
        'source': 'Hypackel'
    })
    return dirname

def main():
    print("Hypackel Games Scraper")
    print("=" * 50)
    print(f"Source: {BASE_URL}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    opener = get_opener()
    
    # Fetch games list
    print("Fetching games.json...")
    try:
        req = urllib.request.Request(GAMES_JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=30) as resp:
            games = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Failed to fetch games: {e}")
        return
    
    print(f"Found {len(games)} games")
    
    games_for_json = []
    scraped = 0
    skipped = 0
    
    for i, game in enumerate(games):
        url = game.get('url', '')
        # Only scrape games with local assets
        if url.startswith('http') and 'hypackel' not in url.lower():
            skipped += 1
            continue
        if '/fork/game/?' in url:
            skipped += 1
            continue
        if '/projects/' in url:
            skipped += 1
            continue
            
        result = scrape_game(opener, game, games_for_json)
        if result:
            scraped += 1
            print(f"  [{scraped}] {game['name']} -> {result}")
        time.sleep(0.3)  # Be nice to the server
    
    print(f"\nScraped {scraped} games, skipped {skipped}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Save games list for merging
    with open(OUTPUT_DIR / '_scraped_games.json', 'w', encoding='utf-8') as f:
        json.dump(games_for_json, f, indent=2)
    
    print(f"Games list saved to {OUTPUT_DIR / '_scraped_games.json'}")

if __name__ == "__main__":
    main()
