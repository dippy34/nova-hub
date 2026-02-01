#!/usr/bin/env python3
"""
Scrape a game from playhop.com
"""
import requests
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

def sanitize_filename(name):
    """Convert name to safe directory name"""
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')

def download_file(url, filepath):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"      Error downloading {url}: {e}", flush=True)
        return False

def extract_game_info(html_content, base_url):
    """Extract game information from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to find title
    title = None
    
    # Try og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title.get('content').strip()
    
    # Try title tag
    if not title:
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
    
    # Try h1
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
    
    # Try to find cover image
    cover_url = None
    
    # Try og:image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        cover_url = og_image.get('content')
        if not cover_url.startswith('http'):
            cover_url = urljoin(base_url, cover_url)
    
    # Try to find game iframe or embed
    iframe = soup.find('iframe')
    game_url = None
    if iframe and iframe.get('src'):
        game_url = iframe.get('src')
        if not game_url.startswith('http'):
            game_url = urljoin(base_url, game_url)
    
    # Try to find game embed in script tags
    if not game_url:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for iframe src or game URLs
                iframe_match = re.search(r'iframe.*?src["\']:\s*["\']([^"\']+)["\']', script.string, re.IGNORECASE)
                if iframe_match:
                    game_url = iframe_match.group(1)
                    if not game_url.startswith('http'):
                        game_url = urljoin(base_url, game_url)
                    break
                
                # Look for game URLs
                game_match = re.search(r'(https?://[^"\']+\.(?:html|swf|unity|js))', script.string)
                if game_match:
                    game_url = game_match.group(1)
                    break
    
    return title, cover_url, game_url

def download_file_with_progress(url, filepath, show_progress=False, current=0, total=0):
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
    game_url = "https://playhop.com/app/477210?utm_source=game_header_logo"
    
    print("Scraping game from playhop.com...")
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
    
    # Extract game info
    print("\nExtracting game information...", flush=True)
    title, cover_url, embedded_game_url = extract_game_info(html_content, game_url)
    
    if not title:
        # Extract from URL
        path = urlparse(game_url).path
        title = path.split('/')[-1].replace('-', ' ').title()
        print("  ⚠ Could not find title, extracted from URL", flush=True)
    else:
        print(f"  ✓ Title: {title}", flush=True)
    
    # Create directory name
    dir_name = sanitize_filename(title)
    if not dir_name or len(dir_name) < 3:
        dir_name = "the-baby-in-yellow-original"
    
    game_dir = GAMES_DIR / dir_name
    print(f"  ✓ Directory: {dir_name}", flush=True)
    
    # Download the actual game page and assets
    print(f"\nDownloading game files...", flush=True)
    game_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch the actual game page HTML
    print("  Fetching game HTML...", flush=True)
    if embedded_game_url:
        try:
            game_r = requests.get(embedded_game_url, headers=HEADERS, timeout=30)
            game_r.raise_for_status()
            game_html = game_r.text
            print(f"    ✓ Fetched {len(game_html)} bytes", flush=True)
        except Exception as e:
            print(f"    ✗ Error fetching game page: {e}", flush=True)
            game_html = html_content
    else:
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
            css_urls.append((urljoin(embedded_game_url or game_url, href), link))
    
    for script in game_soup.find_all('script', src=True):
        src = script.get('src')
        if src and not src.startswith('data:'):
            js_urls.append((urljoin(embedded_game_url or game_url, src), script))
    
    for img in game_soup.find_all('img', src=True):
        src = img.get('src')
        if src and not src.startswith('data:'):
            img_urls.append((urljoin(embedded_game_url or game_url, src), img))
    
    # Find dynamically loaded game scripts
    for script in game_soup.find_all('script'):
        if script.string:
            # Look for Yandex game URLs
            yandex_matches = re.findall(r'https?://[^"\']*yandex[^"\']*\.(?:js|html|wasm)', script.string, re.IGNORECASE)
            for match_url in yandex_matches:
                if match_url not in [url for url, _ in js_urls]:
                    js_urls.append((match_url, script))
            
            # Look for game loader URLs
            loader_matches = re.findall(r'https?://[^"\']+\.(?:js|html|wasm)', script.string, re.IGNORECASE)
            for match_url in loader_matches:
                if 'game' in match_url.lower() or 'loader' in match_url.lower() or 'app-' in match_url.lower():
                    if match_url not in [url for url, _ in js_urls]:
                        js_urls.append((match_url, script))
    
    total_files = len(css_urls) + len(js_urls) + len(img_urls)
    print(f"    Found {len(css_urls)} CSS, {len(js_urls)} JS, {len(img_urls)} images ({total_files} total)", flush=True)
    
    # Download CSS files
    css_files = []
    if css_urls:
        print(f"\n  Downloading CSS files ({len(css_urls)} files)...", flush=True)
        for idx, (css_url, link) in enumerate(css_urls, 1):
            css_filename = Path(urlparse(css_url).path).name or 'style.css'
            css_path = game_dir / css_filename
            if download_file_with_progress(css_url, css_path, show_progress=True, current=idx, total=len(css_urls)):
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
            js_path = game_dir / js_filename
            if download_file_with_progress(js_url, js_path, show_progress=True, current=idx, total=len(js_urls)):
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
            img_path = game_dir / img_filename
            if download_file_with_progress(img_url, img_path, show_progress=True, current=idx, total=len(img_urls)):
                img_files.append(img_filename)
                img['src'] = img_filename
    
    # Remove Yandex SDK references from HTML
    print("\n  Removing Yandex SDK references...", flush=True)
    yandex_removed = 0
    
    # Remove Yandex script tags
    for script in game_soup.find_all('script'):
        src = script.get('src', '')
        if 'yandex' in src.lower() or 'ysdk' in src.lower():
            script.decompose()
            yandex_removed += 1
            print(f"    ✓ Removed Yandex script: {src[:60]}", flush=True)
        
        # Remove Yandex code from inline scripts
        if script.string and ('yandex' in script.string.lower() or 'ysdk' in script.string.lower() or 'YaGames' in script.string):
            # Remove Yandex initialization code
            script.string = re.sub(r'YaGames\.init\([^)]*\)[^;]*;?', '', script.string, flags=re.IGNORECASE)
            script.string = re.sub(r'window\.ysdk\s*=[^;]*;?', '', script.string, flags=re.IGNORECASE)
            script.string = re.sub(r'var\s+ysdk\s*=[^;]*;?', '', script.string, flags=re.IGNORECASE)
            script.string = re.sub(r'ysdk\.[^;]*;?', '', script.string, flags=re.IGNORECASE)
            if script.string.strip():
                yandex_removed += 1
                print(f"    ✓ Cleaned Yandex code from inline script", flush=True)
            else:
                script.decompose()
    
    # Remove Yandex references from downloaded JS files
    print("  Cleaning Yandex references from JS files...", flush=True)
    for js_file in js_files:
        js_path = game_dir / js_file
        if js_path.exists():
            try:
                with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
                    js_content = f.read()
                
                original_len = len(js_content)
                # Remove Yandex SDK calls
                js_content = re.sub(r'YaGames\.init\([^)]*\)[^;]*;?', '', js_content, flags=re.IGNORECASE)
                js_content = re.sub(r'ysdk\.[^;()]*\([^)]*\)[^;]*;?', '', js_content, flags=re.IGNORECASE)
                js_content = re.sub(r'window\.ysdk\s*=[^;]*;?', '', js_content, flags=re.IGNORECASE)
                
                if len(js_content) != original_len:
                    with open(js_path, 'w', encoding='utf-8') as f:
                        f.write(js_content)
                    print(f"    ✓ Cleaned {js_file}", flush=True)
            except Exception as e:
                print(f"    ⚠ Could not clean {js_file}: {e}", flush=True)
    
    # Update base tag
    base_tag = game_soup.find('base')
    if not base_tag:
        base_tag = game_soup.new_tag('base', href='./')
        if game_soup.head:
            game_soup.head.insert(0, base_tag)
    else:
        base_tag['href'] = './'
    
    # Save the modified HTML
    print("\n  Saving HTML...", flush=True)
    html_file = game_dir / "index.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(game_soup))
    print("    ✓ Saved index.html", flush=True)
    
    # Download cover image if found
    if cover_url:
        print(f"  Downloading cover image...", flush=True)
        cover_file = game_dir / "cover.png"
        # Try different extensions
        for ext in ['png', 'jpg', 'jpeg', 'webp']:
            if download_file(cover_url, cover_file):
                print(f"    ✓ Saved cover image", flush=True)
                break
        else:
            print(f"    ⚠ Could not download cover image", flush=True)
    
    # Add to games.json
    print(f"\nAdding to games.json...", flush=True)
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    # Check if already exists
    existing = False
    for game in games:
        if game.get('directory') == dir_name:
            existing = True
            print(f"  ⚠ Game already exists, updating...", flush=True)
            game['name'] = title
            game['directory'] = dir_name
            game['image'] = 'cover.png' if cover_url else 'image.png'
            game['source'] = 'non-semag'
            if cover_url:
                game['imagePath'] = cover_url
            break
    
    if not existing:
        game_info = {
            'name': title,
            'directory': dir_name,
            'image': 'cover.png' if cover_url else 'image.png',
            'source': 'non-semag'
        }
        if cover_url:
            game_info['imagePath'] = cover_url
        games.append(game_info)
        print(f"  ✓ Added new game entry", flush=True)
    
    # Save games.json
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("SCRAPE COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: {title}", flush=True)
    print(f"Directory: {dir_name}", flush=True)
    if embedded_game_url:
        print(f"Embedded game URL: {embedded_game_url}", flush=True)
    print(f"\nDownloaded files:", flush=True)
    print(f"  - CSS: {len(css_files)} files", flush=True)
    print(f"  - JavaScript: {len(js_files)} files", flush=True)
    print(f"  - Images: {len(img_files)} files", flush=True)
    print(f"  - Total assets: {len(css_files) + len(js_files) + len(img_files)} files", flush=True)
    print(f"  - Yandex references removed: {yandex_removed}", flush=True)
    print(f"\nTotal games: {len(games)}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

