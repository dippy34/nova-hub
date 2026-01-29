#!/usr/bin/env python3
"""
Scraper for Undertale game assets from CloudFront
"""
import requests
import os
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path

BASE_URL = "https://d3rtzzzsiu7gdr.cloudfront.net/files/utale/"
OUTPUT_DIR = Path("scraped-utale-assets")

def create_output_dirs():
    """Create output directory structure"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(exist_ok=True)
    (OUTPUT_DIR / "scripts").mkdir(exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(exist_ok=True)
    (OUTPUT_DIR / "other").mkdir(exist_ok=True)

def download_file(url, filepath):
    """Download a file from URL to filepath"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://d3rtzzzsiu7gdr.cloudfront.net/'
        }
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()
        
        total_size = 0
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        print(f"✓ Downloaded: {filepath.name} ({total_size} bytes)")
        return True
    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return False

def scrape_html_assets(html_content):
    """Extract asset URLs from HTML"""
    assets = {
        'images': [],
        'scripts': [],
        'stylesheets': [],
        'favicons': [],
        'other': []
    }
    
    # Find all image sources
    img_patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)',
        r'url\(["\']?([^"\')\s]+\.(png|jpg|jpeg|gif|webp|svg|ico))["\']?\)'
    ]
    
    for pattern in img_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            url = match[0] if isinstance(match, tuple) else match
            if url not in assets['images']:
                assets['images'].append(url)
    
    # Find script sources
    script_pattern = r'<script[^>]+src=["\']([^"\']+)["\']'
    matches = re.findall(script_pattern, html_content, re.IGNORECASE)
    assets['scripts'].extend(matches)
    
    # Find stylesheet links
    css_pattern = r'<link[^>]+href=["\']([^"\']+\.css)["\']'
    matches = re.findall(css_pattern, html_content, re.IGNORECASE)
    assets['stylesheets'].extend(matches)
    
    # Find favicons
    favicon_pattern = r'<link[^>]+rel=["\'](?:icon|shortcut icon)["\'][^>]+href=["\']([^"\']+)["\']'
    matches = re.findall(favicon_pattern, html_content, re.IGNORECASE)
    assets['favicons'].extend(matches)
    
    return assets

def get_file_category(filename):
    """Determine file category based on extension"""
    ext = Path(filename).suffix.lower()
    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.bmp']:
        return 'images'
    elif ext in ['.js', '.mjs']:
        return 'scripts'
    elif ext in ['.css']:
        return 'stylesheets'
    elif ext in ['.wasm', '.data', '.bin']:
        return 'data'
    else:
        return 'other'

def main():
    print("🎮 Undertale Asset Scraper")
    print("=" * 50)
    
    create_output_dirs()
    
    # Known game files from network requests
    known_assets = [
        'runner.js',
        'runner.wasm',
        'runner.data',
        'index.html'
    ]
    
    # Fetch main page
    print(f"\n📄 Fetching {BASE_URL}index.html...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        response = requests.get(BASE_URL + "index.html", timeout=30, headers=headers)
        response.raise_for_status()
        html_content = response.text
        
        # Save HTML
        with open(OUTPUT_DIR / "index.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ Saved index.html")
        
        # Extract assets from HTML
        print("\n🔍 Extracting assets from HTML...")
        html_assets = scrape_html_assets(html_content)
        
        print(f"  Found {len(html_assets['images'])} images")
        print(f"  Found {len(html_assets['scripts'])} scripts")
        print(f"  Found {len(html_assets['stylesheets'])} stylesheets")
        print(f"  Found {len(html_assets['favicons'])} favicons")
        
        # Combine all assets
        all_assets = []
        all_assets.extend(html_assets['images'])
        all_assets.extend(html_assets['scripts'])
        all_assets.extend(html_assets['stylesheets'])
        all_assets.extend(html_assets['favicons'])
        all_assets.extend(known_assets)
        
        # Remove duplicates and normalize URLs
        unique_assets = []
        for asset in all_assets:
            # Make absolute URL if relative
            if asset.startswith('http'):
                url = asset
            elif asset.startswith('/'):
                url = urljoin(BASE_URL, asset)
            else:
                url = urljoin(BASE_URL, asset)
            
            if url not in unique_assets:
                unique_assets.append(url)
        
        # Download all assets
        print(f"\n📥 Downloading {len(unique_assets)} assets...")
        downloaded = 0
        for url in unique_assets:
            filename = os.path.basename(urlparse(url).path) or "index.html"
            category = get_file_category(filename)
            
            if category == 'images':
                filepath = OUTPUT_DIR / "images" / filename
            elif category == 'scripts':
                filepath = OUTPUT_DIR / "scripts" / filename
            elif category == 'data':
                filepath = OUTPUT_DIR / "data" / filename
            else:
                filepath = OUTPUT_DIR / "other" / filename
            
            if download_file(url, filepath):
                downloaded += 1
        
        print(f"\n✅ Complete! Downloaded {downloaded}/{len(unique_assets)} assets")
        print(f"📁 Assets saved to: {OUTPUT_DIR.absolute()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

