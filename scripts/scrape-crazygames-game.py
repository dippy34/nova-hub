#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape a game from crazygames.com
Downloads the game and integrates it into nova-hub
"""
import sys
import io
# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import sys
import os

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Try to import Selenium for dynamic content
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    # Try to use webdriver-manager for automatic ChromeDriver management
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        USE_WEBDRIVER_MANAGER = True
    except ImportError:
        USE_WEBDRIVER_MANAGER = False
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    USE_WEBDRIVER_MANAGER = False
    print("Warning: Selenium not available. Install with: pip install selenium", flush=True)

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def sanitize_filename(name):
    """Convert name to safe directory name"""
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')

def download_file(url, filepath, show_progress=True):
    """Download a file from URL with progress bar"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        total_size = int(r.headers.get('content-length', 0))
        
        if TQDM_AVAILABLE and show_progress and total_size > 0:
            with open(filepath, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"      Downloading {filepath.name}", leave=False) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        else:
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"      ✗ Error downloading {url}: {e}", flush=True)
        return False

def extract_game_info(html_content, base_url):
    """Extract game information from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to find title
    title = None
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()
        # Remove " - CrazyGames" suffix if present
        title = re.sub(r'\s*-\s*CrazyGames.*$', '', title, flags=re.IGNORECASE)
    
    # Try to find meta title
    meta_title = soup.find('meta', property='og:title')
    if meta_title and meta_title.get('content'):
        title = meta_title.get('content').strip()
    
    # Try to find game name in h1
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
    
    # Try to find description
    description = None
    meta_desc = soup.find('meta', property='og:description')
    if meta_desc and meta_desc.get('content'):
        description = meta_desc.get('content').strip()
    
    # Try to find cover image
    cover_url = None
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        cover_url = og_image.get('content')
    
    # Try to find game iframe or embed
    game_url = None
    iframe = soup.find('iframe', {'id': 'game-iframe'}) or soup.find('iframe', class_=re.compile(r'game|embed'))
    if iframe and iframe.get('src'):
        game_url = urljoin(base_url, iframe.get('src'))
    
    # Try to find game URL in script tags
    if not game_url:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for loaderOptions.url (CrazyGames specific)
                loader_matches = re.findall(r'loaderOptions["\']?\s*[:{]\s*[^}]*url["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string)
                if loader_matches:
                    game_url = urljoin(base_url, loader_matches[0])
                    break
                
                # Look for game URL patterns
                url_matches = re.findall(r'["\']([^"\']*game[^"\']*\.html[^"\']*)["\']', script.string, re.IGNORECASE)
                if url_matches:
                    game_url = urljoin(base_url, url_matches[0])
                    break
                
                # Look for embed URL
                embed_matches = re.findall(r'embedUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string)
                if embed_matches:
                    game_url = urljoin(base_url, embed_matches[0])
                    break
    
    return title, description, cover_url, game_url

def extract_game_info_with_selenium(crazygames_url):
    """Use Selenium to extract game information (more reliable for dynamic content)"""
    if not SELENIUM_AVAILABLE:
        return None, None, None, None
    
    try:
        # Setup Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        
        if USE_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        print(f"  Loading page with Selenium...", flush=True)
        driver.get(crazygames_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get page source
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            title = re.sub(r'\s*-\s*CrazyGames.*$', '', title, flags=re.IGNORECASE)
        
        # Extract description
        description = None
        meta_desc = soup.find('meta', property='og:description')
        if meta_desc and meta_desc.get('content'):
            description = meta_desc.get('content').strip()
        
        # Extract cover image
        cover_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            cover_url = og_image.get('content')
        
        # Try to find game iframe
        game_url = None
        try:
            # Wait for iframe to load
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            if iframe:
                game_url = iframe.get_attribute('src')
                if game_url and not game_url.startswith('http'):
                    game_url = urljoin(crazygames_url, game_url)
        except:
            pass
        
        # If no iframe found, try to find game URL in scripts
        if not game_url:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for loaderOptions.url (CrazyGames specific)
                    loader_matches = re.findall(r'loaderOptions["\']?\s*[:{]\s*[^}]*url["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string)
                    if loader_matches:
                        game_url = urljoin(crazygames_url, loader_matches[0])
                        break
                    
                    embed_matches = re.findall(r'embedUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string)
                    if embed_matches:
                        game_url = urljoin(crazygames_url, embed_matches[0])
                        break
        
        driver.quit()
        return title, description, cover_url, game_url
        
    except Exception as e:
        print(f"  ✗ Selenium error: {e}", flush=True)
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        return None, None, None, None

def extract_game_with_selenium(game_url, game_dir):
    """Use Selenium to extract the actual game content"""
    if not SELENIUM_AVAILABLE:
        return None, []
    
    print(f"  Using Selenium to extract actual game content...", flush=True)
    
    # Initialize assets list
    assets_downloaded = []
    
    try:
        # Setup Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        
        if USE_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        print(f"  Loading game URL: {game_url}", flush=True)
        driver.get(game_url)
        
        # Wait for game to load
        print(f"  Waiting for game to load...", flush=True)
        time.sleep(8)
        
        # Get page source
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Download assets found in HTML
        print(f"  Downloading assets from HTML...", flush=True)
        
        # Download scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                asset_url = urljoin(game_url, src)
                asset_path = Path(urlparse(asset_url).path.lstrip('/'))
                local_path = game_dir / asset_path
                if download_file(asset_url, local_path):
                    assets_downloaded.append(str(asset_path))
                    script['src'] = str(asset_path)
        
        # Download stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                asset_url = urljoin(game_url, href)
                asset_path = Path(urlparse(asset_url).path.lstrip('/'))
                local_path = game_dir / asset_path
                if download_file(asset_url, local_path):
                    assets_downloaded.append(str(asset_path))
                    link['href'] = str(asset_path)
        
        # Download images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src and not src.startswith('data:'):
                asset_url = urljoin(game_url, src)
                asset_path = Path(urlparse(asset_url).path.lstrip('/'))
                local_path = game_dir / asset_path
                if download_file(asset_url, local_path):
                    assets_downloaded.append(str(asset_path))
                    img['src'] = str(asset_path)
        
        # Download source elements (for audio/video)
        for source in soup.find_all('source', src=True):
            src = source.get('src')
            if src:
                asset_url = urljoin(game_url, src)
                asset_path = Path(urlparse(asset_url).path.lstrip('/'))
                local_path = game_dir / asset_path
                if download_file(asset_url, local_path):
                    assets_downloaded.append(str(asset_path))
                    source['src'] = str(asset_path)
        
        driver.quit()
        
        # Remove iframes from HTML
        for iframe in soup.find_all('iframe'):
            iframe.decompose()
        
        return str(soup), assets_downloaded
        
    except Exception as e:
        print(f"  ✗ Selenium error: {e}", flush=True)
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        return None, []

def download_game_files(game_url, game_dir):
    """Download game files from the game URL"""
    print(f"  Downloading game files from: {game_url}", flush=True)
    
    try:
        r = requests.get(game_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
    except Exception as e:
        print(f"  ✗ Error fetching game: {e}", flush=True)
        return None, []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    assets_downloaded = []
    
    # Download scripts
    print(f"    Downloading scripts...", flush=True)
    for script in soup.find_all('script', src=True):
        src = script.get('src')
        if src:
            asset_url = urljoin(game_url, src)
            asset_path = Path(urlparse(asset_url).path.lstrip('/'))
            local_path = game_dir / asset_path
            if download_file(asset_url, local_path):
                assets_downloaded.append(str(asset_path))
                script['src'] = str(asset_path)
    
    # Download stylesheets
    print(f"    Downloading stylesheets...", flush=True)
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            asset_url = urljoin(game_url, href)
            asset_path = Path(urlparse(asset_url).path.lstrip('/'))
            local_path = game_dir / asset_path
            if download_file(asset_url, local_path):
                assets_downloaded.append(str(asset_path))
                link['href'] = str(asset_path)
    
    # Download images
    print(f"    Downloading images...", flush=True)
    for img in soup.find_all('img', src=True):
        src = img.get('src')
        if src and not src.startswith('data:'):
            asset_url = urljoin(game_url, src)
            asset_path = Path(urlparse(asset_url).path.lstrip('/'))
            local_path = game_dir / asset_path
            if download_file(asset_url, local_path):
                assets_downloaded.append(str(asset_path))
                img['src'] = str(asset_path)
    
    # Download source elements
    print(f"    Downloading media sources...", flush=True)
    for source in soup.find_all('source', src=True):
        src = source.get('src')
        if src:
            asset_url = urljoin(game_url, src)
            asset_path = Path(urlparse(asset_url).path.lstrip('/'))
            local_path = game_dir / asset_path
            if download_file(asset_url, local_path):
                assets_downloaded.append(str(asset_path))
                source['src'] = str(asset_path)
    
    # Look for assets in script content (Unity WebGL, etc.)
    print(f"    Looking for assets in script content...", flush=True)
    for script in soup.find_all('script'):
        if script.string:
            # Look for Unity WebGL files
            unity_matches = re.findall(r'["\']([^"\']*\.(wasm|data|js|mem|unityweb))["\']', script.string, re.IGNORECASE)
            for match in unity_matches:
                asset_url = urljoin(game_url, match[0])
                asset_path = Path(urlparse(asset_url).path.lstrip('/'))
                local_path = game_dir / asset_path
                if not local_path.exists():
                    if download_file(asset_url, local_path):
                        assets_downloaded.append(str(asset_path))
                        script.string = script.string.replace(match[0], str(asset_path))
    
    # Remove iframes
    for iframe in soup.find_all('iframe'):
        iframe.decompose()
    
    return str(soup), assets_downloaded

def create_game_html(game_html_content, title, base_url, assets_downloaded):
    """Create the final game HTML file"""
    soup = BeautifulSoup(game_html_content, 'html.parser')
    
    # Ensure we have a proper HTML structure
    if not soup.find('html'):
        html = soup.new_tag('html')
        html['lang'] = 'en'
        soup.insert(0, html)
    
    if not soup.find('head'):
        head = soup.new_tag('head')
        soup.html.insert(0, head)
        if not soup.find('meta', charset=True):
            meta_charset = soup.new_tag('meta', charset='utf-8')
            soup.head.insert(0, meta_charset)
        if not soup.find('title'):
            title_tag = soup.new_tag('title')
            title_tag.string = title
            soup.head.append(title_tag)
    
    if not soup.find('body'):
        body = soup.new_tag('body')
        soup.html.append(body)
    
    # Make all asset paths relative
    base_url_parsed = urlparse(base_url)
    
    for tag in soup.find_all(['script', 'link', 'img', 'source']):
        for attr in ['src', 'href']:
            if tag.get(attr):
                url = tag.get(attr)
                if url.startswith('http') and base_url_parsed.netloc in url:
                    # Convert to relative path
                    parsed = urlparse(url)
                    tag[attr] = parsed.path.lstrip('/')
                elif url.startswith('/'):
                    tag[attr] = url.lstrip('/')
    
    return str(soup)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape a game from crazygames.com')
    parser.add_argument('url', nargs='?', default='https://www.crazygames.com/game/slice-master', help='URL of the game page')
    args = parser.parse_args()
    
    game_url = args.url
    
    print("=" * 60, flush=True)
    print("CRAZYGAMES GAME SCRAPER", flush=True)
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Phase 1: Download page HTML
    print("\n[Phase 1/4] Downloading page HTML...", flush=True)
    try:
        print("  Downloading page HTML...", flush=True)
        r = requests.get(game_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
        print(f"  ✓ Fetched {len(html_content):,} bytes", flush=True)
    except Exception as e:
        print(f"  ✗ Error fetching page: {e}", flush=True)
        return
    
    # Phase 2: Extract game info
    print("\n[Phase 2/4] Extracting game information...", flush=True)
    
    # Try Selenium first if available (more reliable for dynamic content)
    if SELENIUM_AVAILABLE:
        print("  Using Selenium to extract game info (more reliable)...", flush=True)
        title, description, cover_url, game_api_url = extract_game_info_with_selenium(game_url)
        if not game_api_url:
            # Fallback to static HTML parsing
            print("  Selenium didn't find game URL, trying static HTML parsing...", flush=True)
            title, description, cover_url, game_api_url = extract_game_info(html_content, game_url)
    else:
        print("  Using static HTML parsing...", flush=True)
        title, description, cover_url, game_api_url = extract_game_info(html_content, game_url)
    
    if not title:
        # Try to extract from URL or use default
        url_match = re.search(r'/game/([^/?]+)', game_url)
        if url_match:
            title = url_match.group(1).replace('-', ' ').title()
        else:
            title = "CrazyGames Game"
        print("  ⚠ Could not find title, using default", flush=True)
    else:
        print(f"  ✓ Title: {title}", flush=True)
    
    if description:
        print(f"  ✓ Description: {description[:100]}...", flush=True)
    
    if cover_url:
        print(f"  ✓ Cover image: {cover_url}", flush=True)
    else:
        print("  ⚠ No cover image found", flush=True)
    
    if game_api_url:
        print(f"  ✓ Game URL: {game_api_url}", flush=True)
    else:
        print("  ⚠ No game URL found, will try to use page directly", flush=True)
        game_api_url = game_url
    
    # Phase 3: Create directory and download game
    print("\n[Phase 3/4] Downloading game files...", flush=True)
    
    dir_name = sanitize_filename(title)
    if not dir_name:
        dir_name = "crazygames-game"
    
    game_dir = GAMES_DIR / dir_name
    game_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ Created directory: {dir_name}", flush=True)
    
    # Try to extract game with Selenium first
    game_html_content = None
    assets_downloaded = []
    
    if SELENIUM_AVAILABLE and game_api_url != game_url:
        game_html_content, assets_downloaded = extract_game_with_selenium(game_api_url, game_dir)
    
    # Fallback to direct download
    if not game_html_content:
        print("  Using direct download method...", flush=True)
        game_html_content, assets_downloaded = download_game_files(game_api_url, game_dir)
    
    if not game_html_content:
        print("  ✗ Failed to download game content", flush=True)
        return
    
    # Create final HTML
    final_html = create_game_html(game_html_content, title, game_api_url, assets_downloaded)
    
    # Save HTML
    html_file = game_dir / "index.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"  ✓ Saved game HTML to {html_file}", flush=True)
    
    # Download cover image
    if cover_url:
        print(f"  Downloading cover image...", flush=True)
        cover_file = game_dir / "cover.png"
        if download_file(cover_url, cover_file):
            print(f"    ✓ Saved cover image", flush=True)
        else:
            print(f"    ⚠ Could not download cover image", flush=True)
    
    # Phase 4: Add to games.json
    print("\n[Phase 4/4] Adding to games.json...", flush=True)
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
            game['url'] = f'non-semag/{dir_name}/index.html'
            game['is_local'] = True
            if description:
                game['description'] = description
            break
    
    if not existing:
        game_info = {
            'name': title,
            'directory': dir_name,
            'image': 'cover.png' if cover_url else 'image.png',
            'source': 'non-semag',
            'url': f'non-semag/{dir_name}/index.html',
            'is_local': True
        }
        if description:
            game_info['description'] = description
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
    print(f"Assets downloaded: {len(assets_downloaded)}", flush=True)
    print(f"Total games: {len(games)}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()
