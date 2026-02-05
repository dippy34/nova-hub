#!/usr/bin/env python3
"""
Scrape a couple games from GameMonetize RSS feed and download them locally (no iframes).
The URL in the JSON is already the game URL - no need to find embed URL.
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import sys

RSS_URL = "https://rss.gamemonetize.com/rssfeed.php?format=json&category=All&type=html5&popularity=newest&company=All&amount=All"
OUTPUT_BASE = Path(__file__).parent.parent / "scraped-gamemonetize-games"
NUM_GAMES = 2

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def sanitize_dirname(name):
    """Convert game title to safe directory name"""
    safe = re.sub(r'[^\w\s\-]', '', name).strip()
    return re.sub(r'\s+', '-', safe).lower()[:50]


def download_file(url, filepath, silent=False):
    """Download a file from URL to filepath"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        if not silent:
            size_kb = filepath.stat().st_size / 1024
            print(f"    [OK] {filepath.name} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        if not silent:
            print(f"    [FAIL] {filepath.name}: {e}")
        return False


def extract_asset_urls(html, base_url):
    """Extract all asset URLs from HTML (scripts, links, images, etc.)"""
    soup = BeautifulSoup(html, 'html.parser')
    urls = set()
    
    # Script src
    for tag in soup.find_all('script', src=True):
        urls.add(urljoin(base_url, tag['src']))
    
    # Link href (stylesheets, etc.)
    for tag in soup.find_all('link', href=True):
        href = tag['href']
        if not href.startswith('data:') and not href.startswith('javascript:'):
            urls.add(urljoin(base_url, href))
    
    # Img src
    for tag in soup.find_all('img', src=True):
        urls.add(urljoin(base_url, tag['src']))
    
    # Source tags (video/audio)
    for tag in soup.find_all('source', src=True):
        urls.add(urljoin(base_url, tag['src']))
    
    # Also parse inline scripts for common patterns (Unity, Phaser, etc.)
    for script in soup.find_all('script'):
        if script.string:
            # Unity WebGL: dataUrl, frameworkUrl, codeUrl, loaderUrl
            patterns = [
                r'["\']([^"\']+\.(js|wasm|data|br|unityweb)[^"\']*)["\']',
                r'(?:dataUrl|frameworkUrl|codeUrl|loaderUrl|streamingAssetsUrl)\s*[:=]\s*["\']([^"\']+)["\']',
                r'src\s*[:=]\s*["\']([^"\']+)["\']',
                r'url\s*[:=]\s*["\']([^"\']+)["\']',
                r'["\'](\./[^"\']+)["\']',
                r'["\']([^"\']+\.(png|jpg|jpeg|gif|webp|mp3|ogg|wav|json))["\']',
            ]
            for pattern in patterns:
                for m in re.finditer(pattern, script.string, re.I):
                    url_cand = m.group(1) if m.lastindex >= 1 else m.group(0)
                    if url_cand and not url_cand.startswith('data:') and not url_cand.startswith('javascript:'):
                        full = urljoin(base_url, url_cand)
                        if 'gamemonetize.com' in full or url_cand.startswith('./') or url_cand.startswith('/'):
                            urls.add(full)
    
    return urls


def url_to_local_path(url, base_url, game_dir):
    """Convert a URL to a local file path relative to game_dir"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        path = 'index.html'
    # Remove game ID from path if it's the first segment (e.g. /8xsm75.../game.js -> game.js)
    parts = path.split('/')
    if len(parts) > 1 and len(parts[0]) > 20:  # Game ID is typically long hash
        parts = parts[1:]
    local_path = game_dir / '/'.join(parts)
    return local_path


def download_game(game_data):
    """Download a single game from GameMonetize"""
    url = game_data.get('url', '').rstrip('/')
    title = game_data.get('title', 'Unknown Game')
    game_id = game_data.get('id', '')
    
    if not url or 'gamemonetize.com' not in url:
        print(f"  [WARN] Invalid URL: {url}")
        return False
    
    # Path ID from URL (e.g. 8xsm75r8jqigepm8fpihn8326rlgpxw5)
    path_id = urlparse(url).path.strip('/').split('/')[-1] or 'game'
    
    # Create directory: scraped-gamemonetize-games/path-id-title
    safe_title = re.sub(r'[^\w\s\-]', '', title).strip()
    safe_title = re.sub(r'\s+', '-', safe_title).lower()[:40]
    dir_name = f"{path_id}-{safe_title}" if safe_title else path_id
    game_dir = OUTPUT_BASE / dir_name
    game_dir.mkdir(parents=True, exist_ok=True)
    
    base_url = url + '/'
    
    print(f"\n  Dir: {game_dir.name}")
    print(f"  URL: {url}")
    
    # 1. Fetch main page (index.html or root)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"  [FAIL] Failed to fetch page: {e}")
        return False
    
    # 2. Extract asset URLs
    asset_urls = extract_asset_urls(html, base_url)
    
    # Filter to same-origin assets only (game files from this game's directory)
    game_asset_urls = set()
    for u in asset_urls:
        if u.startswith(base_url):
            game_asset_urls.add(u)
        elif 'html5.gamemonetize.com' in u and path_id in u:
            game_asset_urls.add(u)
    
    # Add the base index - we need to save the HTML
    # Determine index path - GameMonetize usually serves index.html at /
    index_path = game_dir / 'index.html'
    
    # 3. Rewrite HTML to use local paths
    soup = BeautifulSoup(html, 'html.parser')
    
    def rewrite_url(tag, attr):
        if tag.get(attr):
            orig = tag[attr]
            if orig.startswith('data:') or orig.startswith('javascript:'):
                return
            full_url = urljoin(base_url, orig)
            if full_url.startswith(base_url) or 'html5.gamemonetize.com' in full_url:
                # Make relative: extract path after game ID
                parsed = urlparse(full_url)
                path = parsed.path.strip('/')
                parts = path.split('/')
                if len(parts) > 1 and len(parts[0]) > 20:
                    local = '/'.join(parts[1:]) if len(parts) > 1 else 'index.html'
                else:
                    local = path or 'index.html'
                tag[attr] = local
    
    for tag in soup.find_all('script', src=True):
        rewrite_url(tag, 'src')
    for tag in soup.find_all('link', href=True):
        rewrite_url(tag, 'href')
    for tag in soup.find_all('img', src=True):
        rewrite_url(tag, 'src')
    
    # Save index.html
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"    [OK] index.html")
    
    # 4. Download all assets
    downloaded = 0
    for asset_url in game_asset_urls:
        if asset_url == url or asset_url == base_url or asset_url.rstrip('/') == url:
            continue
        parsed = urlparse(asset_url)
        path = parsed.path.strip('/')
        parts = path.split('/')
        if len(parts) > 1 and len(parts[0]) > 20:
            local_name = '/'.join(parts[1:])
        else:
            local_name = path or 'index.html'
        if local_name == 'index.html':
            continue  # Already saved
        local_path = game_dir / local_name
        if download_file(asset_url, local_path, silent=False):
            downloaded += 1
        time.sleep(0.2)  # Be nice to the server
    
    # 5. Download thumbnail
    thumb = game_data.get('thumb', '')
    if thumb:
        thumb_path = game_dir / 'cover.jpg'
        download_file(thumb, thumb_path, silent=False)
    
    print(f"  [OK] Downloaded {downloaded} assets to {game_dir}")
    return True


def main():
    print("GameMonetize RSS Game Scraper")
    print("=" * 60)
    print(f"Fetching feed: {RSS_URL[:70]}...")
    
    try:
        resp = requests.get(RSS_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        games = resp.json()
    except Exception as e:
        print(f"[FAIL] Failed to fetch RSS: {e}")
        sys.exit(1)
    
    if not isinstance(games, list):
        games = [games] if games else []
    
    # Take first NUM_GAMES
    to_download = games[:NUM_GAMES]
    print(f"[OK] Found {len(games)} games, downloading {len(to_download)}")
    
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    
    for i, game in enumerate(to_download, 1):
        print(f"\n[{i}/{NUM_GAMES}] {game.get('title', 'Unknown')[:50]}")
        download_game(game)
    
    print("\n" + "=" * 60)
    print(f"[OK] Done! Games saved to {OUTPUT_BASE}")


if __name__ == "__main__":
    main()
