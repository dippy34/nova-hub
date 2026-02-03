#!/usr/bin/env python3
"""
Scrape a game from y8.com
"""
import requests
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def download_file(url, filepath, show_progress=False, current=0, total=0):
    """Download a file from URL with progress"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if show_progress and total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r    [{current}/{total}] Downloading {filepath.name}... {percent:.1f}%", end='', flush=True)
        
        if show_progress:
            print(f"\r    [{current}/{total}] ✓ Downloaded {filepath.name} ({downloaded:,} bytes)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"\r    [{current}/{total}] ✗ Error downloading {filepath.name}: {e}", flush=True)
        else:
            print(f"      Error downloading {url}: {e}", flush=True)
        return False

def main():
    game_url = "https://www.y8.com/games/escape_tsunami_for_brainrots"
    
    print("Scraping game from y8.com...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Fetch the page
    print("\nFetching page...", flush=True)
    try:
        r = requests.get(game_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
        print(f"✓ Fetched {len(html_content)} bytes", flush=True)
    except Exception as e:
        print(f"✗ Error fetching page: {e}", flush=True)
        return
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract game information
    print("\nExtracting game information...", flush=True)
    
    # Get title
    title = None
    title_tag = soup.find('h1')
    if title_tag:
        title = title_tag.get_text().strip()
    if not title:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content', '').strip()
    if not title:
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
    
    if not title:
        # Extract from URL
        path = urlparse(game_url).path
        title = path.split('/')[-1].replace('_', ' ').replace('-', ' ').title()
        print("  ⚠ Could not find title, extracted from URL", flush=True)
    else:
        print(f"  ✓ Title: {title}", flush=True)
    
    # Get cover image
    cover_url = None
    og_image = soup.find('meta', property='og:image')
    if og_image:
        cover_url = og_image.get('content', '')
    if not cover_url:
        # Try to find image in page
        img_tag = soup.find('img', class_=re.compile('thumb|cover|game', re.I))
        if img_tag and img_tag.get('src'):
            cover_url = urljoin(game_url, img_tag['src'])
    
    # Find game embed/iframe
    game_embed_url = None
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        game_embed_url = iframe.get('src')
        if not game_embed_url.startswith('http'):
            game_embed_url = urljoin(game_url, game_embed_url)
    
    # Try to find game URL in script tags
    if not game_embed_url:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for game URLs
                match = re.search(r'(https?://[^"\']+\.(?:html|swf|unity|js|wasm))', script.string)
                if match:
                    game_embed_url = match.group(1)
                    break
                
                # Look for iframe src
                iframe_match = re.search(r'iframe.*?src["\']:\s*["\']([^"\']+)["\']', script.string, re.IGNORECASE)
                if iframe_match:
                    game_embed_url = iframe_match.group(1)
                    if not game_embed_url.startswith('http'):
                        game_embed_url = urljoin(game_url, game_embed_url)
                    break
    
    if game_embed_url:
        print(f"  ✓ Found game URL: {game_embed_url}", flush=True)
    else:
        print("  ⚠ Could not find game embed URL", flush=True)
    
    # Create directory
    game_directory = slugify(title)
    if not game_directory or len(game_directory) < 3:
        game_directory = "escape-tsunami-for-brainrots"
    
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ Directory: {game_directory}", flush=True)
    
    # Download game files
    print(f"\nDownloading game files...", flush=True)
    
    if game_embed_url:
        # Fetch the game page
        print("  Fetching game HTML...", flush=True)
        try:
            game_r = requests.get(game_embed_url, headers=HEADERS, timeout=30)
            game_r.raise_for_status()
            game_html = game_r.text
            print(f"    ✓ Fetched {len(game_html)} bytes", flush=True)
        except Exception as e:
            print(f"    ✗ Error fetching game page: {e}", flush=True)
            game_html = html_content
    else:
        game_html = html_content
    
    # Parse game HTML
    game_soup = BeautifulSoup(game_html, 'html.parser')
    
    # Collect assets to download
    print("  Scanning for assets...", flush=True)
    css_urls = []
    js_urls = []
    img_urls = []
    
    # Find CSS files
    for link in game_soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            css_urls.append((urljoin(game_embed_url or game_url, href), link))
    
    # Find JavaScript files
    for script in game_soup.find_all('script', src=True):
        src = script.get('src')
        if src and not src.startswith('data:'):
            js_urls.append((urljoin(game_embed_url or game_url, src), script))
    
    # Find images
    for img in game_soup.find_all('img', src=True):
        src = img.get('src')
        if src and not src.startswith('data:'):
            img_urls.append((urljoin(game_embed_url or game_url, src), img))
    
    # Find dynamically loaded assets in scripts
    for script in game_soup.find_all('script'):
        if script.string:
            # Look for asset URLs
            asset_matches = re.findall(r'https?://[^"\']+\.(?:js|css|png|jpg|jpeg|webp|wasm|data|br)', script.string, re.IGNORECASE)
            for match_url in asset_matches:
                if match_url not in [url for url, _ in css_urls + js_urls + img_urls]:
                    if match_url.endswith(('.css',)):
                        css_urls.append((match_url, None))
                    elif match_url.endswith(('.js', '.wasm', '.data', '.br')):
                        js_urls.append((match_url, None))
                    elif match_url.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        img_urls.append((match_url, None))
    
    total_files = len(css_urls) + len(js_urls) + len(img_urls)
    print(f"    Found {len(css_urls)} CSS, {len(js_urls)} JS, {len(img_urls)} images ({total_files} total)", flush=True)
    
    # Download CSS files
    css_files = []
    if css_urls:
        print(f"\n  Downloading CSS files ({len(css_urls)} files)...", flush=True)
        for idx, (css_url, link) in enumerate(css_urls, 1):
            css_filename = Path(urlparse(css_url).path).name or 'style.css'
            if '?' in css_filename:
                css_filename = css_filename.split('?')[0]
            css_path = game_path / css_filename
            if download_file(css_url, css_path, show_progress=True, current=idx, total=len(css_urls)):
                css_files.append(css_filename)
                if link:
                    link['href'] = css_filename
    
    # Download JavaScript files
    js_files = []
    if js_urls:
        print(f"\n  Downloading JavaScript files ({len(js_urls)} files)...", flush=True)
        for idx, (js_url, script) in enumerate(js_urls, 1):
            js_filename = Path(urlparse(js_url).path).name or 'script.js'
            if '?' in js_filename:
                js_filename = js_filename.split('?')[0]
            js_path = game_path / js_filename
            if download_file(js_url, js_path, show_progress=True, current=idx, total=len(js_urls)):
                js_files.append(js_filename)
                if script:
                    script['src'] = js_filename
    
    # Download images
    img_files = []
    if img_urls:
        print(f"\n  Downloading images ({len(img_urls)} files)...", flush=True)
        for idx, (img_url, img) in enumerate(img_urls, 1):
            img_filename = Path(urlparse(img_url).path).name or 'image.png'
            if '?' in img_filename:
                img_filename = img_filename.split('?')[0]
            img_path = game_path / img_filename
            if download_file(img_url, img_path, show_progress=True, current=idx, total=len(img_urls)):
                img_files.append(img_filename)
                if img:
                    img['src'] = img_filename
    
    # Update base tag
    base_tag = game_soup.find('base')
    if not base_tag:
        base_tag = game_soup.new_tag('base', href='./')
        if game_soup.head:
            game_soup.head.insert(0, base_tag)
    else:
        base_tag['href'] = './'
    
    # Save HTML
    print("\n  Saving HTML...", flush=True)
    html_file = game_path / "index.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(game_soup))
    print("    ✓ Saved index.html", flush=True)
    
    # Download cover image
    if cover_url:
        print(f"\n  Downloading cover image...", flush=True)
        cover_file = game_path / "cover.png"
        if download_file(cover_url, cover_file):
            print("    ✓ Saved cover image", flush=True)
        else:
            print("    ✗ Failed to download cover image", flush=True)
    else:
        print("  ⚠ No cover image found", flush=True)
    
    # Add to games.json
    print(f"\nAdding to games.json...", flush=True)
    games = []
    if GAMES_JSON_PATH.exists():
        with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
            games = json.load(f)
    
    # Check if already exists
    existing = False
    for game in games:
        if game.get('directory') == game_directory:
            existing = True
            game['name'] = title
            game['directory'] = game_directory
            game['image'] = 'cover.png' if cover_url else 'image.png'
            game['source'] = 'non-semag'
            if cover_url:
                game['imagePath'] = cover_url
            break
    
    if not existing:
        game_info = {
            'name': title,
            'directory': game_directory,
            'image': 'cover.png' if cover_url else 'image.png',
            'source': 'non-semag'
        }
        if cover_url:
            game_info['imagePath'] = cover_url
        games.append(game_info)
        print(f"  ✓ Added new game entry", flush=True)
    else:
        print(f"  ✓ Updated existing game entry", flush=True)
    
    # Save games.json
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("SCRAPE COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: {title}", flush=True)
    print(f"Directory: {game_directory}", flush=True)
    if game_embed_url:
        print(f"Game URL: {game_embed_url}", flush=True)
    print(f"\nDownloaded files:", flush=True)
    print(f"  - CSS: {len(css_files)} files", flush=True)
    print(f"  - JavaScript: {len(js_files)} files", flush=True)
    print(f"  - Images: {len(img_files)} files", flush=True)
    print(f"  - Total assets: {len(css_files) + len(js_files) + len(img_files)} files", flush=True)
    print(f"\nTotal games: {len(games)}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()


