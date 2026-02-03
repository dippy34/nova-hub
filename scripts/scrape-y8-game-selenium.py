#!/usr/bin/env python3
"""
Scrape Y8 game using Selenium to capture dynamically loaded files
"""
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

def download_file(url, filepath, show_progress=False, current=0, total=0):
    """Download a file with progress"""
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
                        size_mb = downloaded / 1024 / 1024
                        total_mb = total_size / 1024 / 1024 if total_size > 0 else 0
                        print(f"\r    [{current}/{total}] {filepath.name[:45]:<45} {percent:5.1f}% ({size_mb:.2f}/{total_mb:.2f} MB)", end='', flush=True)
        
        if show_progress:
            size_mb = downloaded / 1024 / 1024
            print(f"\r    [{current}/{total}] ✓ {filepath.name[:45]:<45} ({size_mb:.2f} MB)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"\r    [{current}/{total}] ✗ {filepath.name[:45]:<45} Error", flush=True)
        return False

def main():
    game_url = "https://www.y8.com/embed/escape_tsunami_for_brainrots"
    game_slug = "escape_tsunami_for_brainrots"
    
    print("Scraping Y8 game with Selenium...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Setup Chrome options
    print("\nStep 1: Setting up browser...", flush=True)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Enable performance logging to capture network requests
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("  ✓ Browser started", flush=True)
    except Exception as e:
        print(f"  ✗ Error starting browser: {e}", flush=True)
        print("  ⚠ Make sure ChromeDriver is installed and in PATH", flush=True)
        return
    
    # Create directory
    game_directory = "escape-tsunami-for-brainrots"
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load the page
        print("\nStep 2: Loading game page...", flush=True)
        driver.get(game_url)
        print(f"  ✓ Page loaded: {driver.title}", flush=True)
        
        # Wait for game to start loading
        print("  Waiting for game to load...", flush=True)
        time.sleep(5)  # Wait for initial load
        
        # Get performance logs to capture network requests
        print("\nStep 3: Capturing network requests...", flush=True)
        logs = driver.get_log('performance')
        
        game_files = []
        seen_urls = set()
        
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                if method == 'Network.responseReceived':
                    response = message.get('message', {}).get('params', {}).get('response', {})
                    url = response.get('url', '')
                    mime_type = response.get('mimeType', '')
                    
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        
                        # Filter for game files
                        if any(x in url.lower() for x in ['.js', '.wasm', '.data', '.framework', '.loader', '.unity', '.br']):
                            if not any(x in url.lower() for x in ['newrelic', 'analytics', 'account', 'profile', 'privacy']):
                                game_files.append(('js', url))
                        elif any(x in url.lower() for x in ['.css']):
                            if not any(x in url.lower() for x in ['newrelic', 'analytics']):
                                game_files.append(('css', url))
                        elif any(x in url.lower() for x in ['.png', '.jpg', '.jpeg', '.webp', '.svg']):
                            if not any(x in url.lower() for x in ['newrelic', 'analytics', 'logo', 'icon']):
                                game_files.append(('img', url))
                        elif any(x in url.lower() for x in ['.json', '.bin']):
                            game_files.append(('other', url))
                
                elif method == 'Network.requestWillBeSent':
                    request = message.get('message', {}).get('params', {}).get('request', {})
                    url = request.get('url', '')
                    
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        
                        # Look for Unity/WebGL files
                        if any(x in url.lower() for x in ['.wasm', '.data', '.framework', '.loader', '.unity', '.br']):
                            if not any(x in url.lower() for x in ['newrelic', 'analytics', 'account', 'profile']):
                                game_files.append(('unity', url))
            except:
                continue
        
        # Also get page source to find additional files
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find script tags
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and src not in seen_urls:
                seen_urls.add(src)
                if not any(x in src.lower() for x in ['newrelic', 'analytics']):
                    game_files.append(('js', src))
        
        # Find CSS
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href and href not in seen_urls:
                seen_urls.add(href)
                if not any(x in href.lower() for x in ['newrelic', 'analytics']):
                    game_files.append(('css', href))
        
        # Find images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src and src not in seen_urls and not src.startswith('data:'):
                seen_urls.add(src)
                if not any(x in src.lower() for x in ['newrelic', 'analytics', 'logo', 'icon']):
                    game_files.append(('img', href))
        
        # Remove duplicates
        game_files = list(set(game_files))
        
        print(f"  ✓ Found {len(game_files)} game files", flush=True)
        
        # Download files
        print(f"\nStep 4: Downloading game files ({len(game_files)} files)...", flush=True)
        downloaded = []
        
        for idx, (file_type, file_url) in enumerate(game_files, 1):
            # Make URL absolute
            if not file_url.startswith('http'):
                file_url = urljoin(game_url, file_url)
            
            filename = Path(urlparse(file_url).path).name
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename or filename == '/':
                ext = {'css': 'css', 'js': 'js', 'img': 'png', 'unity': 'wasm', 'other': 'bin'}.get(file_type, 'bin')
                filename = f"game_{idx}.{ext}"
            
            filepath = game_path / filename
            
            if download_file(file_url, filepath, show_progress=True, current=idx, total=len(game_files)):
                downloaded.append((file_type, filename, file_url))
        
        # Get page HTML
        print("\nStep 5: Saving game HTML...", flush=True)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update file references in HTML
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                filename = Path(urlparse(src).path).name
                if '?' in filename:
                    filename = filename.split('?')[0]
                if filename in [f[1] for f in downloaded]:
                    script['src'] = filename
        
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                filename = Path(urlparse(href).path).name
                if '?' in filename:
                    filename = filename.split('?')[0]
                if filename in [f[1] for f in downloaded]:
                    link['href'] = filename
        
        # Add base tag
        base_tag = soup.find('base')
        if not base_tag:
            base_tag = soup.new_tag('base', href='./')
            if soup.head:
                soup.head.insert(0, base_tag)
        else:
            base_tag['href'] = './'
        
        # Save HTML
        html_file = game_path / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"  ✓ Saved index.html", flush=True)
        
        # Download cover
        print("\nStep 6: Downloading cover image...", flush=True)
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
            if cover_url:
                cover_file = game_path / "cover.png"
                if download_file(cover_url, cover_file):
                    print("  ✓ Saved cover.png", flush=True)
        
    except Exception as e:
        print(f"\n✗ Error: {e}", flush=True)
    finally:
        driver.quit()
        print("\n  ✓ Browser closed", flush=True)
    
    # Update games.json
    print("\nStep 7: Updating games.json...", flush=True)
    games = []
    if GAMES_JSON_PATH.exists():
        with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
            games = json.load(f)
    
    existing = False
    for game in games:
        if game.get('directory') == game_directory:
            existing = True
            game['name'] = "Escape Tsunami for Brainrots"
            game['image'] = 'cover.png'
            break
    
    if not existing:
        games.append({
            'name': "Escape Tsunami for Brainrots",
            'directory': game_directory,
            'image': 'cover.png',
            'source': 'non-semag'
        })
    
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("DOWNLOAD COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Files downloaded: {len(downloaded)}", flush=True)
    print(f"  - CSS: {len([f for f in downloaded if f[0] == 'css'])}", flush=True)
    print(f"  - JavaScript: {len([f for f in downloaded if f[0] == 'js'])}", flush=True)
    print(f"  - Images: {len([f for f in downloaded if f[0] == 'img'])}", flush=True)
    print(f"  - Unity/Other: {len([f for f in downloaded if f[0] in ['unity', 'other']])}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    main()


