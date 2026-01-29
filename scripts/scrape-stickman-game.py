#!/usr/bin/env python3
"""
Scraper for Stickman Destruction 3 Heroes - Only game files, no website assets
"""
import requests
import os
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path

# Game-specific URLs (extracted from network requests)
GAME_BASE_URL = "https://files.crazygames.com/stickman-destruction-3-heroes/6/Build/"
GAME_HTML_URL = "https://stickman-destruction-3-heroes.game-files.crazygames.com/unity/unity2020/stickman-destruction-3-heroes.html"
OUTPUT_DIR = Path("scraped-stickman-game")

def create_output_dirs():
    """Create output directory structure"""
    OUTPUT_DIR.mkdir(exist_ok=True)

def download_file(url, filepath):
    """Download a file from URL to filepath"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.crazygames.com/'
        }
        response = requests.get(url, stream=True, timeout=60, headers=headers)
        response.raise_for_status()
        
        total_size = 0
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        print(f"✓ Downloaded: {filepath.name} ({total_size:,} bytes)")
        return True
    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return False

def scrape_game_html(html_url):
    """Extract game file references from the Unity HTML file"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.crazygames.com/'
        }
        response = requests.get(html_url, timeout=30, headers=headers)
        response.raise_for_status()
        html_content = response.text
        
        # Save the HTML
        with open(OUTPUT_DIR / "index.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ Saved index.html")
        
        # Extract Unity game files (loader, framework, wasm, data)
        game_files = []
        
        # Find loader.js
        loader_pattern = r'["\']([^"\']*loader\.js)["\']'
        matches = re.findall(loader_pattern, html_content, re.IGNORECASE)
        game_files.extend(matches)
        
        # Find framework.js
        framework_pattern = r'["\']([^"\']*framework\.js[^"\']*)["\']'
        matches = re.findall(framework_pattern, html_content, re.IGNORECASE)
        game_files.extend(matches)
        
        # Find .wasm files
        wasm_pattern = r'["\']([^"\']*\.wasm[^"\']*)["\']'
        matches = re.findall(wasm_pattern, html_content, re.IGNORECASE)
        game_files.extend(matches)
        
        # Find .data files
        data_pattern = r'["\']([^"\']*\.data[^"\']*)["\']'
        matches = re.findall(data_pattern, html_content, re.IGNORECASE)
        game_files.extend(matches)
        
        # Find .mem files
        mem_pattern = r'["\']([^"\']*\.mem[^"\']*)["\']'
        matches = re.findall(mem_pattern, html_content, re.IGNORECASE)
        game_files.extend(matches)
        
        return list(set(game_files))  # Remove duplicates
        
    except Exception as e:
        print(f"❌ Error fetching game HTML: {e}")
        return []

def main():
    print("🎮 Stickman Destruction 3 Heroes - Game Files Scraper")
    print("=" * 60)
    print("⚠️  Only downloading game files, NOT website assets")
    print()
    
    create_output_dirs()
    
    # Known Unity game files (from network requests)
    known_files = [
        "bl3.loader.js",
        "bl3.framework.js.br",
        "bl3.wasm.br",
        "bl3.data.br"
    ]
    
    print(f"📄 Fetching game HTML from {GAME_HTML_URL}...")
    html_files = scrape_game_html(GAME_HTML_URL)
    
    # Combine known files with files found in HTML
    all_files = list(set(known_files + html_files))
    
    # Remove .br extension for actual filenames (brotli compressed)
    # We'll download both compressed and uncompressed versions if available
    files_to_download = []
    for f in all_files:
        # Remove .br extension to get base filename
        base_file = f.replace('.br', '')
        files_to_download.append(base_file)
        # Also try compressed version
        if not f.endswith('.br'):
            files_to_download.append(f + '.br')
    
    # Remove duplicates
    files_to_download = list(set(files_to_download))
    
    print(f"\n📥 Downloading {len(files_to_download)} game files from {GAME_BASE_URL}...")
    downloaded = 0
    
    for filename in files_to_download:
        # Try both compressed and uncompressed
        for variant in [filename, filename + '.br']:
            url = urljoin(GAME_BASE_URL, variant)
            filepath = OUTPUT_DIR / variant
            
            if download_file(url, filepath):
                downloaded += 1
                break  # Success, move to next file
    
    print(f"\n✅ Complete! Downloaded {downloaded}/{len(files_to_download)} game files")
    print(f"📁 Game files saved to: {OUTPUT_DIR.absolute()}")
    print(f"\n💡 The game can be played by opening: {OUTPUT_DIR / 'index.html'}")

if __name__ == "__main__":
    main()

