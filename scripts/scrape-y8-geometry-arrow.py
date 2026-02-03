#!/usr/bin/env python3
"""
Scrape Geometry Arrow from Y8.com using Selenium
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
from bs4 import BeautifulSoup
import requests

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

def sanitize_filename(name):
    """Sanitize filename"""
    return re.sub(r'[^\w\-_\.]', '_', name).lower()

def download_file(url, filepath, show_progress=False, current=0, total=0):
    """Download a file with progress"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=60)
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
            print(f"\r    [{current}/{total}] ✗ {filepath.name[:45]:<45} Error: {str(e)[:30]}", flush=True)
        return False

def main():
    game_url = "https://www.y8.com/games/geometry_arrow"
    game_name = "Geometry Arrow"
    game_directory = sanitize_filename("geometry-arrow")
    
    print("Scraping Geometry Arrow from Y8.com...")
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
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load the page
        print("\nStep 2: Loading game page...", flush=True)
        driver.get(game_url)
        print(f"  ✓ Page loaded: {driver.title}", flush=True)
        
        # Wait for game iframe to load
        print("  Waiting for game to load...", flush=True)
        time.sleep(3)
        
        # Try to find and switch to iframe
        try:
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            iframe_src = iframe.get_attribute("src")
            print(f"  Found iframe: {iframe_src}", flush=True)
            driver.switch_to.frame(iframe)
            time.sleep(5)  # Wait for game to load in iframe
        except:
            print("  No iframe found, continuing on main page", flush=True)
        
        # Get performance logs to capture network requests
        print("\nStep 3: Capturing network requests...", flush=True)
        logs = driver.get_log('performance')
        
        unity_files = []
        seen_urls = set()
        
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                
                if method == 'Network.responseReceived':
                    response = message.get('message', {}).get('params', {}).get('response', {})
                    url = response.get('url', '')
                    
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        
                        # Filter for Unity WebGL build files
                        if re.search(r'\.(wasm|data|framework|loader)\.js(\.unityweb)?(\.br)?$', url, re.IGNORECASE):
                            if not any(x in url.lower() for x in ['newrelic', 'analytics', 'account', 'profile', 'privacy']):
                                unity_files.append(url)
            except:
                continue
        
        # Also check page source for Unity files
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find script tags that might reference Unity files
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if src and src not in seen_urls:
                seen_urls.add(src)
                if re.search(r'\.(wasm|data|framework|loader)\.js(\.unityweb)?(\.br)?$', src, re.IGNORECASE):
                    if not src.startswith('http'):
                        src = urljoin(game_url, src)
                    unity_files.append(src)
        
        # Remove duplicates
        unity_files = list(set(unity_files))
        
        print(f"  ✓ Found {len(unity_files)} Unity WebGL file(s)", flush=True)
        for url in unity_files[:5]:  # Show first 5
            print(f"    - {url[:80]}", flush=True)
        
        # Download Unity files
        print(f"\nStep 4: Downloading Unity WebGL files ({len(unity_files)} files)...", flush=True)
        downloaded_files = []
        
        for idx, file_url in enumerate(unity_files, 1):
            filename = Path(urlparse(file_url).path).name
            if not filename or filename == '/':
                filename = f"unity_file_{idx}.js"
            
            filepath = game_path / filename
            
            if download_file(file_url, filepath, show_progress=True, current=idx, total=len(unity_files)):
                downloaded_files.append(filename)
        
        # Get cover image
        print("\nStep 5: Downloading cover image...", flush=True)
        try:
            driver.switch_to.default_content()  # Switch back to main page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            og_image = soup.find('meta', property='og:image')
            if og_image:
                cover_url = og_image.get('content', '')
                if cover_url:
                    cover_file = game_path / "cover.png"
                    if download_file(cover_url, cover_file):
                        print("  ✓ Saved cover.png", flush=True)
        except Exception as e:
            print(f"  ⚠ Could not download cover: {e}", flush=True)
        
        # Create HTML wrapper
        print("\nStep 6: Creating HTML wrapper...", flush=True)
        
        # Find the loader script
        loader_script = None
        for f in downloaded_files:
            if 'loader' in f.lower():
                loader_script = f
                break
        
        if not loader_script and downloaded_files:
            loader_script = downloaded_files[0]
        
        # Find data, framework, and wasm files
        data_file = next((f for f in downloaded_files if '.data' in f.lower()), None)
        framework_file = next((f for f in downloaded_files if '.framework' in f.lower()), None)
        wasm_file = next((f for f in downloaded_files if '.wasm' in f.lower()), None)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{game_name}</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: #000;
        }}
        #unity-container {{
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        #unity-canvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}
    </style>
</head>
<body>
    <div id="unity-container">
        <canvas id="unity-canvas"></canvas>
    </div>
"""
        
        if loader_script:
            html_content += f'    <script src="{loader_script}"></script>\n'
        
        html_content += f"""    <script>
        createUnityInstance(document.querySelector("#unity-canvas"), {{
"""
        
        if data_file:
            html_content += f'            dataUrl: "{data_file}",\n'
        if framework_file:
            html_content += f'            frameworkUrl: "{framework_file}",\n'
        if wasm_file:
            html_content += f'            codeUrl: "{wasm_file}",\n'
        
        html_content += f"""            companyName: "Y8",
            productName: "{game_name}",
            productVersion: "1.0",
            showBanner: function(msg, type) {{
                if (type === "error") {{
                    console.error("Unity Error: " + msg);
                }} else {{
                    console.log("Unity: " + msg);
                }}
            }}
        }}).then(function(instance) {{
            console.log("Unity instance created");
        }}).catch(function(error) {{
            console.error("Failed to create Unity instance:", error);
        }});
    </script>
</body>
</html>"""
        
        html_file = game_path / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"  ✓ Saved index.html", flush=True)
        
    except Exception as e:
        print(f"\n✗ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("\n  ✓ Browser closed", flush=True)
    
    # Update games.json
    print("\nStep 7: Updating games.json...", flush=True)
    if GAMES_JSON_PATH.exists():
        with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
            games_data = json.load(f)
    else:
        games_data = {"games": []}
    
    # Remove existing entry if it exists
    games_data["games"] = [g for g in games_data["games"] if g.get("directory") != game_directory]
    
    # Add new entry
    game_entry = {
        "name": game_name,
        "directory": game_directory,
        "image": "cover.png",
        "source": "non-semag",
        "url": f"non-semag/{game_directory}/index.html",
        "is_local": True
    }
    games_data["games"].append(game_entry)
    
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(games_data, f, indent='\t', ensure_ascii=False)
    
    print("  ✓ Updated games.json", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("DOWNLOAD COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: {game_name}", flush=True)
    print(f"Directory: {game_directory}", flush=True)
    print(f"Unity files downloaded: {len(downloaded_files)}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()


