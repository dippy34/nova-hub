#!/usr/bin/env python3
"""
Scrape a game from addictinggames.com
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
    'Referer': 'https://www.addictinggames.com/',
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
            print(f"    ✗ Error downloading {url}: {e}", flush=True)
        return False

def main():
    game_url = "https://www.addictinggames.com/sports/golf-mania"
    
    print("Scraping game from addictinggames.com...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}\n", flush=True)
    
    # 1. Fetch the game page
    print("Fetching page...", flush=True)
    try:
        r = requests.get(game_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
        print(f"✓ Fetched {len(html_content)} bytes", flush=True)
    except Exception as e:
        print(f"✗ Error fetching {game_url}: {e}", flush=True)
        return
    
    # 2. Extract game information
    print("\nExtracting game information...", flush=True)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get title
    title_tag = soup.find('meta', property='og:title') or soup.find('title') or soup.find('h1')
    if title_tag:
        if hasattr(title_tag, 'get'):
            game_title = title_tag.get('content', '') or title_tag.get_text().strip()
        else:
            game_title = title_tag.get_text().strip()
    else:
        game_title = "Golf Mania"
    
    print(f"  ✓ Title: {game_title}", flush=True)
    
    game_directory = slugify(game_title)
    if not game_directory:
        game_directory = "golf-mania"
    print(f"  ✓ Directory: {game_directory}", flush=True)
    
    # Find the embedded game URL
    embedded_game_url = None
    
    # Look for iframe with game content
    iframe = soup.find('iframe', class_='game-iframe') or soup.find('iframe', id='game-iframe') or soup.find('iframe')
    if iframe and iframe.get('src'):
        src = iframe['src']
        # Skip JS files, look for HTML/embed URLs
        if not src.endswith('.js') and ('html' in src.lower() or 'embed' in src.lower() or 'game' in src.lower()):
            embedded_game_url = src
            if not embedded_game_url.startswith('http'):
                embedded_game_url = urljoin(game_url, embedded_game_url)
    
    # Look in script tags for game embed URLs
    if not embedded_game_url:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for embed URLs or game HTML URLs
                match = re.search(r'(https?://[^"\']+/(?:embed|game|play)[^"\']*\.(?:html|php))', script.string, re.IGNORECASE)
                if match:
                    embedded_game_url = match.group(1)
                    break
                
                # Look for iframe src in scripts
                match = re.search(r'iframe.*?src["\']:\s*["\']([^"\']+)["\']', script.string, re.IGNORECASE)
                if match:
                    potential_url = match.group(1)
                    # Skip JS files
                    if not potential_url.endswith('.js'):
                        embedded_game_url = potential_url
                        if not embedded_game_url.startswith('http'):
                            embedded_game_url = urljoin(game_url, embedded_game_url)
                        break
                
                # Look for gameId and construct embed URL
                match = re.search(r'gameId["\']:\s*["\']([^"\']+)["\']', script.string)
                if match:
                    game_id = match.group(1)
                    # Try common Addicting Games embed patterns
                    potential_urls = [
                        f"https://www.addictinggames.com/embed/{game_id}",
                        f"https://www.addictinggames.com/game/{game_id}",
                        f"https://www.addictinggames.com/play/{game_id}",
                    ]
                    # Test which one works (we'll use the first one for now)
                    embedded_game_url = potential_urls[0]
                    break
    
    # If still not found, try to find the game container and use the page itself
    if not embedded_game_url:
        # Check if there's a game container that loads the game dynamically
        game_container = soup.find('div', class_=re.compile('game|play', re.I)) or soup.find('div', id=re.compile('game|play', re.I))
        if game_container:
            # Use the original page URL as embed
            embedded_game_url = game_url
    
    if not embedded_game_url:
        print("  ✗ Could not find embedded game URL.", flush=True)
        return
    
    print(f"  ✓ Found embedded game URL: {embedded_game_url}", flush=True)
    
    # 3. Download the actual game page and assets
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    print("\nDownloading game files...", flush=True)
    
    # Fetch the actual game page HTML
    print("  Fetching game HTML...", flush=True)
    try:
        game_r = requests.get(embedded_game_url, headers=HEADERS, timeout=30)
        game_r.raise_for_status()
        game_html = game_r.text
        print(f"    ✓ Fetched {len(game_html)} bytes", flush=True)
    except Exception as e:
        print(f"    ✗ Error fetching game page: {e}", flush=True)
        # Fallback to original page
        game_html = html_content
    
    # Parse the game HTML to find assets
    game_soup = BeautifulSoup(game_html, 'html.parser')
    
    # First, collect all files to download
    print("  Scanning for assets...", flush=True)
    css_urls = []
    js_urls = []
    img_urls = []
    
    for link in game_soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            css_urls.append((urljoin(embedded_game_url, href), link))
    
    for script in game_soup.find_all('script', src=True):
        src = script.get('src')
        if src and not src.startswith('data:'):
            js_urls.append((urljoin(embedded_game_url, src), script))
    
    for img in game_soup.find_all('img', src=True):
        src = img.get('src')
        if src and not src.startswith('data:'):
            img_urls.append((urljoin(embedded_game_url, src), img))
    
    total_files = len(css_urls) + len(js_urls) + len(img_urls)
    print(f"    Found {len(css_urls)} CSS, {len(js_urls)} JS, {len(img_urls)} images ({total_files} total)", flush=True)
    
    # Download CSS files
    css_files = []
    if css_urls:
        print(f"\n  Downloading CSS files ({len(css_urls)} files)...", flush=True)
        for idx, (css_url, link) in enumerate(css_urls, 1):
            css_filename = Path(urlparse(css_url).path).name or 'style.css'
            css_path = game_path / css_filename
            if download_file(css_url, css_path, show_progress=True, current=idx, total=len(css_urls)):
                css_files.append(css_filename)
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
                img['src'] = img_filename
    
    # Find and download dynamically loaded game scripts (like mowgoats.com loaders)
    print(f"\n  Scanning for dynamically loaded game scripts...", flush=True)
    game_loader_urls = []
    
    # Look for script tags that dynamically load game files
    for script in game_soup.find_all('script'):
        script_content = script.string or ''
        # Look for o.src= patterns (common for dynamic script loading)
        match = re.search(r'o\.src\s*=\s*["\']([^"\']+\.(?:js|html|wasm))["\']', script_content, re.IGNORECASE)
        if match:
            loader_url = match.group(1)
            if loader_url not in [url for url, _ in game_loader_urls]:
                game_loader_urls.append((loader_url, script))
        
        # Also look for other patterns
        loader_matches = re.findall(r'https?://[^"\']+\.(?:js|html|wasm)', script_content, re.IGNORECASE)
        for match_url in loader_matches:
            if ('mowgoats' in match_url.lower() or 'game' in match_url.lower() or 'loader' in match_url.lower()) and match_url not in [url for url, _ in game_loader_urls]:
                game_loader_urls.append((match_url, script))
    
    if game_loader_urls:
        print(f"    Found {len(game_loader_urls)} game loader script(s)", flush=True)
        print(f"\n  Downloading game loader scripts ({len(game_loader_urls)} files)...", flush=True)
        for idx, (loader_url, script) in enumerate(game_loader_urls, 1):
            loader_filename = Path(urlparse(loader_url).path).name or 'game-loader.js'
            if '?' in loader_filename:
                loader_filename = loader_filename.split('?')[0]
            # Sanitize filename - handle URL-encoded characters
            loader_filename = re.sub(r'[^\w\.-]', '_', loader_filename)
            if not loader_filename.endswith('.js'):
                loader_filename += '.js'
            loader_path = game_path / loader_filename
            
            if download_file(loader_url, loader_path, show_progress=True, current=idx, total=len(game_loader_urls)):
                # Update the script to use local path
                if script.string:
                    # Replace the URL in the script content
                    script.string = script.string.replace(loader_url, loader_filename)
                    print(f"    ✓ Updated script to use local {loader_filename}", flush=True)
                if loader_filename not in js_files:
                    js_files.append(loader_filename)
    
    # Update base tag or add one to handle relative URLs
    base_tag = game_soup.find('base')
    if not base_tag:
        base_tag = game_soup.new_tag('base', href='./')
        if game_soup.head:
            game_soup.head.insert(0, base_tag)
    else:
        base_tag['href'] = './'
    
    # Save the modified HTML
    print("\n  Saving HTML...", flush=True)
    with open(game_path / "index.html", 'w', encoding='utf-8') as f:
        f.write(str(game_soup))
    print("    ✓ Saved index.html", flush=True)
    
    # 4. Download cover image
    cover_image_url = soup.find('meta', property='og:image')
    if cover_image_url and 'content' in cover_image_url.attrs:
        cover_image_url = cover_image_url['content']
        print("  Downloading cover image...", flush=True)
        if download_file(cover_image_url, game_path / "cover.png"):
            print("    ✓ Saved cover image", flush=True)
        else:
            print("    ✗ Failed to download cover image.", flush=True)
    else:
        print("  ✗ No cover image found.", flush=True)
    
    # 5. Add to games.json
    print("\nAdding to games.json...", flush=True)
    games = []
    if GAMES_JSON_PATH.exists():
        with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
            games = json.load(f)
    
    # Check if already exists
    existing = False
    for game in games:
        if game.get('directory') == game_directory:
            existing = True
            game['name'] = game_title
            game['image'] = "cover.png"
            game['source'] = "non-semag"
            if cover_image_url:
                game['imagePath'] = cover_image_url
            break
    
    if not existing:
        new_game_entry = {
            "name": game_title,
            "directory": game_directory,
            "image": "cover.png",
            "source": "non-semag",
            "imagePath": cover_image_url if cover_image_url else ""
        }
        games.append(new_game_entry)
        print("  ✓ Added new game entry", flush=True)
    else:
        print("  ✓ Updated existing game entry", flush=True)
    
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("SCRAPE COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: {game_title}", flush=True)
    print(f"Directory: {game_directory}", flush=True)
    print(f"Embedded game URL: {embedded_game_url}", flush=True)
    print(f"\nDownloaded files:", flush=True)
    print(f"  - CSS: {len(css_files)} files", flush=True)
    print(f"  - JavaScript: {len(js_files)} files", flush=True)
    print(f"  - Images: {len(img_files)} files", flush=True)
    print(f"  - Total assets: {len(css_files) + len(js_files) + len(img_files)} files", flush=True)
    print(f"\nTotal games: {len(games)}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

