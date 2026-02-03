#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape a game from poki.com
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
    """Download a file from URL with progress indicator"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        filename = filepath.name
        
        if TQDM_AVAILABLE and show_progress and total_size > 0:
            # Use tqdm for progress bar
            with open(filepath, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc=f"      {filename[:40]:<40}", leave=False) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pbar.update(len(chunk))
        else:
            # Simple progress without tqdm
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if show_progress and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r      {filename[:40]:<40} {percent:.1f}%", end='', flush=True)
        
        if show_progress and not TQDM_AVAILABLE and total_size > 0:
            print()  # New line after progress
        
        return True
    except Exception as e:
        print(f"\n      ✗ Error downloading {url}: {e}", flush=True)
        return False

def extract_game_info_with_selenium(poki_url):
    """Use Selenium to extract game info from Poki page (more reliable)"""
    if not SELENIUM_AVAILABLE:
        return None, None, None, None, None
    
    print("    [1/4] Initializing browser...", flush=True)
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        
        # Use webdriver-manager if available, otherwise try default
        if USE_WEBDRIVER_MANAGER:
            print("    [2/4] Downloading/checking ChromeDriver...", flush=True)
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        try:
            print("    [3/4] Loading Poki page and waiting for content...", flush=True)
            driver.get(poki_url)
            time.sleep(3)  # Wait for page to load
            
            print("    [4/4] Extracting game information...", flush=True)
            # Get page source after JavaScript execution
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = None
            title_elem = soup.select_one('meta[property="og:title"]')
            if title_elem:
                title = title_elem.get('content', '').strip()
                title = re.sub(r'\s*-\s*Poki.*$', '', title, flags=re.IGNORECASE).strip()
            
            # Extract description
            description = None
            desc_elem = soup.select_one('meta[property="og:description"]')
            if desc_elem:
                description = desc_elem.get('content', '').strip()
            
            # Extract cover image
            cover_url = None
            img_elem = soup.select_one('meta[property="og:image"]')
            if img_elem:
                cover_url = img_elem.get('content', '')
            
            # Extract game API URL from iframe
            game_api_url = None
            try:
                wait = WebDriverWait(driver, 10)
                iframe = wait.until(EC.presence_of_element_located((By.ID, "game-element")))
                game_api_url = iframe.get_attribute('src')
                print(f"    ✓ Found game iframe", flush=True)
            except:
                # Try to find iframe in HTML
                iframe = soup.find('iframe', id='game-element')
                if iframe:
                    game_api_url = iframe.get('src', '')
                    print(f"    ✓ Found game iframe in HTML", flush=True)
            
            return title, description, cover_url, game_api_url, None
            
        finally:
            print("    Closing browser...", flush=True)
            driver.quit()
            
    except Exception as e:
        print(f"    ✗ Selenium error: {e}", flush=True)
        return None, None, None, None, None

def extract_game_info(html_content, base_url):
    """Extract game information from Poki HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title
    title = None
    title_selectors = [
        'meta[property="og:title"]',
        'meta[name="title"]',
        'h1',
        'title'
    ]
    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            title = elem.get('content', '') or elem.text.strip()
            if title:
                # Clean up title (remove " - Poki" suffix if present)
                title = re.sub(r'\s*-\s*Poki.*$', '', title, flags=re.IGNORECASE)
                title = title.strip()
                break
    
    # Extract description
    description = None
    desc_elem = soup.select_one('meta[property="og:description"]')
    if desc_elem:
        description = desc_elem.get('content', '').strip()
    
    # Extract cover image
    cover_url = None
    img_elem = soup.select_one('meta[property="og:image"]')
    if img_elem:
        cover_url = img_elem.get('content', '')
        if cover_url and not cover_url.startswith('http'):
            cover_url = urljoin('https://poki.com', cover_url)
    
    # Extract game API URL - this is the actual playable game
    game_api_url = None
    game_id = None
    
    # Method 1: Try to find iframe with id='game-element' (this is the actual game)
    iframe = soup.find('iframe', id='game-element')
    if iframe and iframe.get('src'):
        game_api_url = iframe.get('src')
        if not game_api_url.startswith('http'):
            game_api_url = urljoin('https://poki.com', game_api_url)
        # This is the actual game URL, use it directly
        return title, description, cover_url, game_api_url, game_id
    
    # Method 2: Extract game ID from URL and construct CDN URL
    if not game_api_url:
        # Poki game URLs are like: https://poki.com/en/g/level-devil
        # Extract the game slug (last part after /g/)
        url_match = re.search(r'/g/([^/?]+)', base_url)
        if url_match:
            game_slug = url_match.group(1)
            # Try to find game ID in page data
            # Look for game data in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for game ID patterns
                    id_match = re.search(r'"gameId"\s*:\s*"([^"]+)"', script.string)
                    if id_match:
                        game_id = id_match.group(1)
                        break
                    # Also try looking for game-cdn URLs
                    cdn_match = re.search(r'game-cdn\.poki\.com/([^/]+)', script.string)
                    if cdn_match:
                        game_id = cdn_match.group(1)
                        break
            
            # If we found a game ID, construct the CDN URL
            if game_id:
                game_api_url = f"https://game-cdn.poki.com/{game_id}/index.html"
            else:
                # Fallback: try constructing with slug (some games use slug as ID)
                game_api_url = f"https://game-cdn.poki.com/{game_slug}/index.html"
    
    # Method 3: Look for game data in JSON-LD or other structured data
    if not game_api_url:
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld and json_ld.string:
            try:
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and 'game' in data:
                    game_data = data.get('game', {})
                    if 'gameId' in game_data:
                        game_id = game_data['gameId']
                        game_api_url = f"https://game-cdn.poki.com/{game_id}/index.html"
            except:
                pass
    
    # Method 4: Look in window.__INITIAL_STATE__ or similar
    if not game_api_url:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('__INITIAL_STATE__' in script.string or 'gameId' in script.string):
                # Try to extract game ID from JavaScript
                id_matches = re.findall(r'gameId["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string)
                if id_matches:
                    game_id = id_matches[0]
                    game_api_url = f"https://game-cdn.poki.com/{game_id}/index.html"
                    break
    
    return title, description, cover_url, game_api_url, game_id

def extract_game_with_selenium(poki_url, game_dir):
    """Use Selenium to extract the actual game content from Poki page"""
    if not SELENIUM_AVAILABLE:
        return None, []
    
    print(f"  Using Selenium to extract actual game content...", flush=True)
    
    try:
        # Setup Chrome with DevTools Protocol enabled
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        # Enable logging
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # Use webdriver-manager if available, otherwise try default
        if USE_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Load the Poki game page
            print(f"    [1/6] Loading Poki page...", flush=True)
            driver.get(poki_url)
            time.sleep(2)
            
            # Wait for the game iframe to load
            print(f"    [2/6] Waiting for game iframe...", flush=True)
            wait = WebDriverWait(driver, 30)
            iframe = wait.until(EC.presence_of_element_located((By.ID, "game-element")))
            
            # Get the iframe src (this is the actual game URL)
            iframe_src = iframe.get_attribute('src')
            print(f"    ✓ Found iframe src: {iframe_src[:80]}...", flush=True)
            
            # Enable network domain to intercept requests
            print(f"    [3/6] Enabling network interception...", flush=True)
            try:
                driver.execute_cdp_cmd('Network.enable', {})
                driver.execute_cdp_cmd('Page.enable', {})
            except:
                pass
            
            # Load the iframe URL directly and wait for the actual game
            print(f"    Loading game URL directly and waiting for game to load...", flush=True)
            driver.get(iframe_src)
            
            # Collect network requests
            network_requests = []
            game_files = []
            
            # Wait a long time for the game to actually load
            print(f"    Waiting for game to initialize and capture network requests...", flush=True)
            for i in range(20):  # Wait up to 20 seconds, checking every second
                time.sleep(1)
                try:
                    # Get performance logs
                    logs = driver.get_log('performance')
                    for log in logs:
                        try:
                            message = json.loads(log['message'])
                            method = message.get('message', {}).get('method', '')
                            params = message.get('message', {}).get('params', {})
                            
                            if method == 'Network.responseReceived':
                                response = params.get('response', {})
                                url = response.get('url', '')
                                mime_type = response.get('mimeType', '')
                                
                                # Look for game files
                                if url and any(ext in url.lower() for ext in ['.js', '.wasm', '.data', '.png', '.jpg', '.json', '.css', '.html']):
                                    if url not in network_requests:
                                        network_requests.append(url)
                                        # Check if it's a game file
                                        if any(indicator in url.lower() for indicator in ['game', 'level', 'devil', 'poki', 'cdn', 'build', 'asset']):
                                            game_files.append(url)
                                            print(f"      Found game file: {url[:80]}...", flush=True)
                        except:
                            pass
                except:
                    pass
                
                # Check if game has loaded
                try:
                    canvas = driver.find_element(By.TAG_NAME, "canvas")
                    if canvas:
                        print(f"    ✓ Game canvas found after {i+1} seconds", flush=True)
                        break
                except:
                    pass
            
            # Wait for document ready
            try:
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            except:
                pass
            
            # Look for actual game content - try multiple strategies
            print(f"    Looking for game content...", flush=True)
            game_loaded = False
            
            # Strategy 1: Look for canvas
            try:
                canvas = driver.find_element(By.TAG_NAME, "canvas")
                if canvas:
                    print(f"    ✓ Found canvas element", flush=True)
                    game_loaded = True
            except:
                pass
            
            # Strategy 2: Look for game container or iframe
            try:
                game_container = driver.find_element(By.CSS_SELECTOR, "[id*='game'], [class*='game'], [id*='Game'], [class*='Game']")
                if game_container:
                    print(f"    ✓ Found game container", flush=True)
                    game_loaded = True
            except:
                pass
            
            # Strategy 3: Check if there's an inner iframe with the actual game
            try:
                inner_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                if inner_iframes:
                    print(f"    Found {len(inner_iframes)} inner iframe(s), switching to first one...", flush=True)
                    driver.switch_to.frame(inner_iframes[0])
                    time.sleep(5)
                    # Check for game content in inner iframe
                    try:
                        canvas = driver.find_element(By.TAG_NAME, "canvas")
                        if canvas:
                            print(f"    ✓ Found canvas in inner iframe", flush=True)
                            game_loaded = True
                    except:
                        pass
            except:
                pass
            
            # Wait more if game seems to be loading
            if not game_loaded:
                print(f"    Game may still be loading, waiting longer...", flush=True)
                time.sleep(10)
            
            # Get the actual game HTML
            print(f"    [4/6] Extracting game HTML...", flush=True)
            game_html = driver.page_source
            game_url = driver.current_url
            print(f"    Game URL: {game_url[:100]}...", flush=True)
            
            # Also try to get the innerHTML of body to see actual content
            try:
                body_html = driver.execute_script("return document.body.innerHTML")
                if body_html and len(body_html) > 1000:  # If we got substantial content
                    print(f"    ✓ Got substantial body content ({len(body_html)} chars)", flush=True)
                    # Use body HTML if it's more substantial
                    if len(body_html) > len(game_html) * 0.5:
                        game_html = f"<html><head></head><body>{body_html}</body></html>"
            except:
                pass
            
            # Wait a bit more for any dynamic content
            time.sleep(3)
            
            # Try executing JavaScript to get more info
            try:
                # Get all script sources
                script_sources = driver.execute_script("""
                    return Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
                """)
                print(f"    Found {len(script_sources)} script sources via JS", flush=True)
            except:
                pass
            
            # Parse the game HTML
            game_soup = BeautifulSoup(game_html, 'html.parser')
            
            # Remove any iframes from the game HTML - we want NO iframes
            for iframe_tag in game_soup.find_all('iframe'):
                iframe_tag.decompose()
            
            # Also remove any redirect scripts or links
            for script in game_soup.find_all('script'):
                script_text = script.string or ''
                if 'window.location' in script_text or 'document.location' in script_text or 'redirect' in script_text.lower():
                    # This might be a redirect script, but keep it for now in case it's needed
                    pass
            
            # Get the base URL for downloading assets
            parsed_url = urlparse(game_url)
            # Try to find the actual game base URL
            base_cdn_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            if parsed_url.path:
                path_parts = parsed_url.path.split('/')
                # Try different base URLs
                if len(path_parts) > 1:
                    base_cdn_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(path_parts[:-1])}"
            if not base_cdn_url.endswith('/'):
                base_cdn_url += '/'
            
            print(f"    [6/6] Base URL: {base_cdn_url}", flush=True)
            
            # Download game files found via network interception
            print(f"    [5/6] Found {len(game_files)} game files from network", flush=True)
            if game_files:
                print(f"    Downloading game files (prioritizing actual game files)...", flush=True)
                # Prioritize actual game files (from gdn.poki.com or game-cdn.poki.com)
                prioritized_files = []
                other_files = []
                for url in game_files:
                    if 'gdn.poki.com' in url or 'game-cdn.poki.com' in url or any(ext in url for ext in ['.wasm', '.data', '.unityweb']):
                        prioritized_files.append(url)
                    else:
                        other_files.append(url)
                
                # Download prioritized files first, then others (limit to 100 total)
                files_to_download = prioritized_files[:50] + other_files[:50]
                print(f"    Downloading {len(files_to_download)} files (prioritized: {len(prioritized_files)})", flush=True)
                
                for i, game_file_url in enumerate(files_to_download, 1):
                    try:
                        # Extract filename
                        file_path = urlparse(game_file_url).path.lstrip('/')
                        if not file_path or file_path == '/':
                            # Generate a name from query params or URL
                            if '.js' in game_file_url:
                                file_path = f"game_{i}.js"
                            elif '.wasm' in game_file_url:
                                file_path = f"game_{i}.wasm"
                            elif '.data' in game_file_url:
                                file_path = f"game_{i}.data"
                            elif '.css' in game_file_url:
                                file_path = f"game_{i}.css"
                            else:
                                file_path = f"game_file_{i}"
                        
                        # Clean up path
                        file_path = file_path.replace('..', '').lstrip('/')
                        # Preserve directory structure but make it safe
                        if '/' in file_path:
                            parts = file_path.split('/')
                            file_path = '/'.join(p.replace('..', '') for p in parts)
                        
                        local_path = game_dir / file_path
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        print(f"      [{i}/{len(files_to_download)}] {file_path[:60]}", flush=True)
                        if download_file(game_file_url, local_path, show_progress=False):
                            assets_downloaded.append(file_path)
                        else:
                            print(f"        ✗ Download failed", flush=True)
                    except Exception as e:
                        print(f"        ✗ Error: {e}", flush=True)
                
                print(f"    ✓ Downloaded {len(assets_downloaded)} game files from network", flush=True)
            
            # Also try to extract game files using JavaScript
            print(f"    [6/6] Extracting additional assets via JavaScript...", flush=True)
            try:
                # Get all script sources
                script_sources = driver.execute_script("""
                    var scripts = [];
                    document.querySelectorAll('script[src]').forEach(function(s) {
                        scripts.push(s.src);
                    });
                    return scripts;
                """)
                if script_sources:
                    print(f"    Found {len(script_sources)} script sources", flush=True)
                    for src in script_sources[:5]:  # Show first 5
                        print(f"      - {src[:80]}...", flush=True)
                
                # Get all link sources (CSS, etc.)
                link_sources = driver.execute_script("""
                    var links = [];
                    document.querySelectorAll('link[href]').forEach(function(l) {
                        links.push(l.href);
                    });
                    return links;
                """)
                if link_sources:
                    print(f"    Found {len(link_sources)} link sources", flush=True)
                
                # Get all image sources
                img_sources = driver.execute_script("""
                    var imgs = [];
                    document.querySelectorAll('img[src]').forEach(function(i) {
                        imgs.push(i.src);
                    });
                    return imgs;
                """)
                if img_sources:
                    print(f"    Found {len(img_sources)} image sources", flush=True)
                
            except Exception as e:
                print(f"    Could not extract via JS: {e}", flush=True)
            
            assets_downloaded = []
            
            # Collect all assets first - be more aggressive
            scripts = list(game_soup.find_all('script', src=True))
            # Also look for inline scripts that might load assets
            inline_scripts = game_soup.find_all('script')
            stylesheets = list(game_soup.find_all('link', rel='stylesheet', href=True))
            # Also look for link tags with other rel types
            stylesheets.extend(game_soup.find_all('link', href=True))
            images = list(game_soup.find_all('img', src=True))
            # Also look for background images in style attributes
            for tag in game_soup.find_all(style=True):
                style = tag.get('style', '')
                if 'url(' in style:
                    # Extract URL from style
                    import re
                    urls = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
                    for url in urls:
                        if url.startswith('http') or url.startswith('//'):
                            # This is an image URL
                            pass
            
            total_assets = len(scripts) + len(stylesheets) + len(images)
            
            print(f"    Found {total_assets} assets to download:", flush=True)
            print(f"      - {len(scripts)} scripts", flush=True)
            print(f"      - {len(stylesheets)} stylesheets", flush=True)
            print(f"      - {len(images)} images", flush=True)
            
            # Download scripts
            if scripts:
                print(f"\n    [6/6] Downloading {len(scripts)} scripts...", flush=True)
                for i, script in enumerate(scripts, 1):
                    src = script.get('src', '')
                    if src:
                        if not src.startswith('http'):
                            if src.startswith('//'):
                                src = 'https:' + src
                            else:
                                src = urljoin(base_cdn_url, src)
                        # Download the script
                        script_path = urlparse(src).path.lstrip('/')
                        if not script_path:
                            # Use a default name
                            script_path = f"script_{i}.js"
                        # Make path safe
                        script_path = script_path.replace('..', '').lstrip('/')
                        local_path = game_dir / script_path
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        print(f"      [{i}/{len(scripts)}] {script_path[:50]}", flush=True)
                        if download_file(src, local_path, show_progress=False):
                            assets_downloaded.append(script_path)
                            # Update the src to be relative
                            script['src'] = script_path
                        else:
                            print(f"        ✗ Failed to download", flush=True)
            
            # Download stylesheets
            if stylesheets:
                print(f"\n    Downloading {len(stylesheets)} stylesheets...", flush=True)
                for i, link in enumerate(stylesheets, 1):
                    href = link.get('href', '')
                    if href:
                        if not href.startswith('http'):
                            if href.startswith('//'):
                                href = 'https:' + href
                            else:
                                href = urljoin(base_cdn_url, href)
                        # Download the stylesheet
                        css_path = urlparse(href).path.lstrip('/')
                        if not css_path:
                            css_path = f"style_{i}.css"
                        css_path = css_path.replace('..', '').lstrip('/')
                        local_path = game_dir / css_path
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        print(f"      [{i}/{len(stylesheets)}] {css_path[:50]}", flush=True)
                        if download_file(href, local_path, show_progress=False):
                            assets_downloaded.append(css_path)
                            # Update the href to be relative
                            link['href'] = css_path
            
            # Download images
            if images:
                print(f"\n    Downloading {len(images)} images...", flush=True)
                for i, img in enumerate(images, 1):
                    src = img.get('src', '')
                    if src and not src.startswith('data:'):
                        if not src.startswith('http'):
                            if src.startswith('//'):
                                src = 'https:' + src
                            else:
                                src = urljoin(base_cdn_url, src)
                        # Download the image
                        img_path = urlparse(src).path.lstrip('/')
                        if not img_path:
                            img_path = f"image_{i}.png"
                        img_path = img_path.replace('..', '').lstrip('/')
                        local_path = game_dir / img_path
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        print(f"      [{i}/{len(images)}] {img_path[:50]}", flush=True)
                        if download_file(src, local_path, show_progress=False):
                            assets_downloaded.append(img_path)
                            # Update the src to be relative
                            img['src'] = img_path
            
            # Also try to extract game data from JavaScript
            # Look for game files in script tags
            for script in game_soup.find_all('script'):
                script_text = script.string
                if script_text:
                    # Look for common game file patterns
                    import re
                    # Look for .js, .wasm, .data files
                    game_files = re.findall(r'["\']([^"\']+\.(?:js|wasm|data|json|png|jpg|jpeg|gif|svg))["\']', script_text)
                    for game_file in game_files[:10]:  # Limit to first 10
                        if game_file.startswith('http') or game_file.startswith('//'):
                            # Download this file
                            if game_file.startswith('//'):
                                game_file = 'https:' + game_file
                            file_path = urlparse(game_file).path.lstrip('/')
                            if file_path:
                                file_path = file_path.replace('..', '').lstrip('/')
                                local_path = game_dir / file_path
                                local_path.parent.mkdir(parents=True, exist_ok=True)
                                if download_file(game_file, local_path, show_progress=False):
                                    assets_downloaded.append(file_path)
            
            return str(game_soup), assets_downloaded
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"    ✗ Error with Selenium: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None, []

def download_game_files(game_api_url, game_dir):
    """Download the actual game files from Poki CDN"""
    print(f"  [Step 1/4] Fetching game HTML from CDN...", flush=True)
    print(f"    URL: {game_api_url}", flush=True)
    
    try:
        # Fetch the game's main HTML file
        print("    Downloading...", flush=True)
        r = requests.get(game_api_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        game_html = r.text
        print(f"    ✓ Downloaded {len(game_html)} bytes", flush=True)
        
        # Check if we got an error page
        if 'AccessDenied' in game_html or 'Access Denied' in game_html:
            print(f"    ✗ CDN blocked access (403 Forbidden)", flush=True)
            return None, []
        
        # Parse the game HTML
        print(f"  [Step 2/4] Parsing HTML and finding assets...", flush=True)
        game_soup = BeautifulSoup(game_html, 'html.parser')
        
        # Get the base URL for the game (directory on CDN)
        parsed_url = urlparse(game_api_url)
        base_cdn_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}"
        if not base_cdn_url.endswith('/'):
            base_cdn_url += '/'
        
            # Find and download all assets
            assets_downloaded = []
            
            # Collect all assets first
        scripts = list(game_soup.find_all('script', src=True))
        stylesheets = list(game_soup.find_all('link', rel='stylesheet', href=True))
        images = list(game_soup.find_all('img', src=True))
        total_assets = len(scripts) + len(stylesheets) + len(images)
        
        print(f"    Found {total_assets} assets:", flush=True)
        print(f"      - {len(scripts)} scripts", flush=True)
        print(f"      - {len(stylesheets)} stylesheets", flush=True)
        print(f"      - {len(images)} images", flush=True)
        
        # Download scripts
        if scripts:
            print(f"  [Step 3/4] Downloading {len(scripts)} scripts...", flush=True)
            for i, script in enumerate(scripts, 1):
                src = script.get('src', '')
                if src:
                    if not src.startswith('http'):
                        src = urljoin(base_cdn_url, src)
                    # Download the script
                    script_path = urlparse(src).path.lstrip('/')
                    if not script_path:
                        continue
                    local_path = game_dir / script_path
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    print(f"    [{i}/{len(scripts)}] Script: {script_path}", flush=True)
                    if download_file(src, local_path):
                        assets_downloaded.append(script_path)
                        # Update the src to be relative
                        script['src'] = script_path
        
        # Download stylesheets
        if stylesheets:
            print(f"\n  Downloading {len(stylesheets)} stylesheets...", flush=True)
            for i, link in enumerate(stylesheets, 1):
                href = link.get('href', '')
                if href:
                    if not href.startswith('http'):
                        href = urljoin(base_cdn_url, href)
                    # Download the stylesheet
                    css_path = urlparse(href).path.lstrip('/')
                    if not css_path:
                        continue
                    local_path = game_dir / css_path
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    print(f"    [{i}/{len(stylesheets)}] Stylesheet: {css_path}", flush=True)
                    if download_file(href, local_path):
                        assets_downloaded.append(css_path)
                        # Update the href to be relative
                        link['href'] = css_path
        
        # Download images
        if images:
            print(f"\n  Downloading {len(images)} images...", flush=True)
            for i, img in enumerate(images, 1):
                src = img.get('src', '')
                if src and not src.startswith('data:'):
                    if not src.startswith('http'):
                        src = urljoin(base_cdn_url, src)
                    # Download the image
                    img_path = urlparse(src).path.lstrip('/')
                    if not img_path:
                        continue
                    local_path = game_dir / img_path
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    print(f"    [{i}/{len(images)}] Image: {img_path}", flush=True)
                    if download_file(src, local_path):
                        assets_downloaded.append(img_path)
                        # Update the src to be relative
                        img['src'] = img_path
        
        print(f"  [Step 4/4] Saving modified HTML...", flush=True)
        
        # Save the modified HTML
        modified_html = str(game_soup)
        return modified_html, assets_downloaded
        
    except Exception as e:
        print(f"    ✗ Error downloading game files: {e}", flush=True)
        return None, []

def main():
    game_url = "https://poki.com/en/g/level-devil"
    
    print("Scraping game from poki.com...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Fetch the page
    print("\n[Phase 1/4] Fetching Poki game page...", flush=True)
    print(f"  URL: {game_url}", flush=True)
    try:
        print("  Downloading page HTML...", flush=True)
        r = requests.get(game_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
        print(f"  ✓ Fetched {len(html_content):,} bytes", flush=True)
    except Exception as e:
        print(f"  ✗ Error fetching page: {e}", flush=True)
        return
    
    # Extract game info
    print("\n[Phase 2/4] Extracting game information...", flush=True)
    
    # Try Selenium first if available (more reliable for dynamic content)
    if SELENIUM_AVAILABLE:
        print("  Using Selenium to extract game info (more reliable)...", flush=True)
        title, description, cover_url, game_api_url, game_id = extract_game_info_with_selenium(game_url)
        if not game_api_url:
            # Fallback to static HTML parsing
            print("  Selenium didn't find game, trying static HTML parsing...", flush=True)
            title, description, cover_url, game_api_url, game_id = extract_game_info(html_content, game_url)
    else:
        print("  Using static HTML parsing...", flush=True)
        title, description, cover_url, game_api_url, game_id = extract_game_info(html_content, game_url)
    
    if not title:
        # Try to extract from URL or use default
        url_match = re.search(r'/g/([^/?]+)', game_url)
        if url_match:
            title = url_match.group(1).replace('-', ' ').title()
        else:
            title = "Poki Game"
        print(f"  ⚠ Could not find title, using: {title}", flush=True)
    else:
        print(f"  ✓ Title: {title}", flush=True)
    
    if not game_api_url:
        print("  ✗ Could not find game API URL", flush=True)
        print("  Trying alternative methods...", flush=True)
        
        # Last resort: try common Poki CDN patterns
        url_match = re.search(r'/g/([^/?]+)', game_url)
        if url_match:
            game_slug = url_match.group(1)
            # Try a few common patterns
            possible_urls = [
                f"https://game-cdn.poki.com/{game_slug}/index.html",
                f"https://game-cdn.poki.com/g/{game_slug}/index.html",
            ]
            for url in possible_urls:
                # Test if URL exists
                try:
                    test_r = requests.head(url, headers=HEADERS, timeout=5, allow_redirects=True)
                    if test_r.status_code == 200:
                        game_api_url = url
                        print(f"  ✓ Found game at: {game_api_url}", flush=True)
                        break
                except:
                    continue
        
        if not game_api_url:
            print("  ✗ Could not determine game URL. The game may require JavaScript to load.", flush=True)
            print("  You may need to use Selenium to extract the game URL.", flush=True)
            return
    
    print(f"  ✓ Game API URL: {game_api_url}", flush=True)
    
    if cover_url:
        print(f"  ✓ Cover image: {cover_url}", flush=True)
    else:
        print("  ⚠ No cover image found", flush=True)
    
    # Create directory name
    dir_name = sanitize_filename(title)
    if not dir_name:
        dir_name = "poki-game"
    
    game_dir = GAMES_DIR / dir_name
    print(f"  ✓ Directory: {dir_name}", flush=True)
    
    # Download game files
    print(f"\n[Phase 3/4] Downloading game files...", flush=True)
    html_file = game_dir / "index.html"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Always use Selenium to get the actual game content
    game_html = None
    assets = []
    
    if SELENIUM_AVAILABLE:
        print(f"  Using Selenium to extract actual game content (no iframes)...", flush=True)
        game_html, assets = extract_game_with_selenium(game_url, game_dir)
    
    # If Selenium didn't work, try direct download as fallback
    if not game_html:
        print(f"  Selenium extraction failed, trying direct download...", flush=True)
        game_html, assets = download_game_files(game_api_url, game_dir)
    
    if game_html:
        print(f"  Processing and saving game files...", flush=True)
        # Update title in the HTML if possible
        game_soup = BeautifulSoup(game_html, 'html.parser')
        title_tag = game_soup.find('title')
        if title_tag:
            title_tag.string = title
        else:
            # Add title if it doesn't exist
            head = game_soup.find('head')
            if not head:
                head = game_soup.new_tag('head')
                game_soup.html.insert(0, head)
            new_title = game_soup.new_tag('title')
            new_title.string = title
            head.insert(0, new_title)
        
        # Save the game HTML
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(game_soup))
        file_size = os.path.getsize(html_file)
        print(f"  ✓ Saved game HTML ({file_size:,} bytes) to {html_file}", flush=True)
        if assets:
            print(f"  ✓ Successfully downloaded {len(assets)} asset(s)", flush=True)
    else:
        print(f"  ✗ Failed to download game files", flush=True)
        print(f"  Note: Poki's CDN may block direct access. The game may need to be loaded via iframe.", flush=True)
        return
    
    # Download cover image if found
    print(f"\n[Phase 4/4] Finalizing...", flush=True)
    if cover_url:
        print(f"  Downloading cover image...", flush=True)
        cover_file = game_dir / "cover.png"
        if download_file(cover_url, cover_file):
            cover_size = os.path.getsize(cover_file)
            print(f"  ✓ Saved cover image ({cover_size:,} bytes)", flush=True)
        else:
            print(f"  ⚠ Could not download cover image", flush=True)
            # Create a placeholder
            cover_file = game_dir / "cover.png"
            cover_file.touch()
    else:
        print(f"  ⚠ No cover image URL found", flush=True)
    
    # Add to games.json
    print(f"  Updating games.json...", flush=True)
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
            game['image'] = 'cover.png'
            game['source'] = 'non-semag'
            if description:
                game['description'] = description
            break
    
    if not existing:
        game_info = {
            'name': title,
            'directory': dir_name,
            'image': 'cover.png',
            'source': 'non-semag'
        }
        if description:
            game_info['description'] = description
        games.append(game_info)
        print(f"  ✓ Added new game entry", flush=True)
    
    # Save games.json
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print(f"  ✓ Updated games.json", flush=True)
    
    # Calculate total size
    total_size = 0
    if html_file.exists():
        total_size += os.path.getsize(html_file)
    cover_file = game_dir / "cover.png"
    if cover_file.exists():
        total_size += os.path.getsize(cover_file)
    # Add asset sizes
    if assets:
        for asset in assets:
            asset_path = game_dir / asset
            if asset_path.exists():
                total_size += os.path.getsize(asset_path)
    
    print("\n" + "=" * 60, flush=True)
    print("✓ SCRAPE COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game Name: {title}", flush=True)
    print(f"Directory: {dir_name}", flush=True)
    print(f"Game URL: {game_api_url}", flush=True)
    print(f"Files Downloaded: {len(assets) + 1} (HTML + {len(assets)} assets)", flush=True)
    print(f"Total Size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)", flush=True)
    print(f"Cover Image: {'✓ Downloaded' if cover_url else '✗ Not found'}", flush=True)
    print(f"Total Games in Database: {len(games)}", flush=True)
    print(f"✓ Successfully added to games.json", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    main()

