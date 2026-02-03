#!/usr/bin/env python3
"""
Try to scrape Kill the Spartan by accessing files directly
"""
import json
import re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

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
            print(f"\r    [{current}/{total}] ✗ {filepath.name[:45]:<45} Error", flush=True)
        return False

def main():
    base_url = "https://shsgames.github.io/g/4ead5539/kill-the-spartan"
    game_name = "Kill the Spartan"
    game_directory = "kill-the-spartan"
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    print("Trying to access game files directly...")
    print("=" * 60, flush=True)
    
    # Try common Unity WebGL file patterns
    print("\nStep 1: Testing common Unity file paths...", flush=True)
    common_files = [
        "Build/loader.js",
        "build/loader.js",
        "loader.js",
        "Build/Build.loader.js",
        "build/build.loader.js",
        "index.html",
    ]
    
    found_files = []
    for filename in common_files:
        test_url = f"{base_url}/{filename}"
        try:
            r = requests.head(test_url, headers=HEADERS, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                found_files.append((filename, test_url))
                print(f"  ✓ Found: {filename}", flush=True)
        except:
            pass
    
    # If we found a loader, try to get the HTML and parse it
    if found_files:
        print(f"\nStep 2: Found {len(found_files)} file(s), downloading...", flush=True)
        for idx, (filename, url) in enumerate(found_files, 1):
            filepath = game_path / Path(filename).name
            download_file(url, filepath, show_progress=True, current=idx, total=len(found_files))
        
        # Try to get index.html to find more files
        index_url = f"{base_url}/index.html"
        try:
            r = requests.get(index_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                # Find Unity files in the HTML
                for script in soup.find_all('script', src=True):
                    src = script.get('src')
                    if src and any(x in src.lower() for x in ['.loader', '.framework', '.wasm', '.data']):
                        full_url = urljoin(index_url, src)
                        filename = Path(src).name
                        filepath = game_path / filename
                        if not filepath.exists():
                            found_files.append((filename, full_url))
                            download_file(full_url, filepath, show_progress=True, current=len(found_files), total=len(found_files)+1)
        except:
            pass
    
    # If still no files, try GitHub raw content
    if not found_files:
        print("\nStep 2: Trying GitHub raw content...", flush=True)
        github_base = "https://raw.githubusercontent.com/shsgames/shsgames.github.io/main/g/4ead5539/kill-the-spartan"
        for filename in common_files:
            test_url = f"{github_base}/{filename}"
            try:
                r = requests.head(test_url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    found_files.append((filename, test_url))
                    print(f"  ✓ Found on GitHub: {filename}", flush=True)
            except:
                pass
    
    if not found_files:
        print("\n✗ Could not find any game files. The game may not exist at this URL.")
        print("  Please verify the URL is correct.")
        return
    
    # Download all found files
    print(f"\nStep 3: Downloading {len(found_files)} file(s)...", flush=True)
    downloaded = []
    for idx, (filename, url) in enumerate(found_files, 1):
        filepath = game_path / Path(filename).name
        if download_file(url, filepath, show_progress=True, current=idx, total=len(found_files)):
            downloaded.append(Path(filename).name)
    
    print(f"\n✓ Downloaded {len(downloaded)} file(s)", flush=True)
    print("Note: You may need to manually check the game files and create a proper HTML wrapper.")

if __name__ == "__main__":
    main()


