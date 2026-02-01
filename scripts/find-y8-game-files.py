#!/usr/bin/env python3
"""
Find and download only the game files from Y8.com
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
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

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
                        size_mb = downloaded / 1024 / 1024
                        total_mb = total_size / 1024 / 1024 if total_size > 0 else 0
                        print(f"\r    [{current}/{total}] {filepath.name[:50]:<50} {percent:5.1f}% ({size_mb:.2f}/{total_mb:.2f} MB)", end='', flush=True)
        
        if show_progress:
            size_mb = downloaded / 1024 / 1024
            print(f"\r    [{current}/{total}] ✓ {filepath.name[:50]:<50} ({size_mb:.2f} MB)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"\r    [{current}/{total}] ✗ {filepath.name[:50]:<50} Error: {e}", flush=True)
        return False

def find_game_files(page_url):
    """Find the actual game files from Y8 page"""
    print("  Fetching page...", flush=True)
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        content = r.text
        print(f"    ✓ Fetched {len(content):,} bytes", flush=True)
    except Exception as e:
        print(f"    ✗ Error: {e}", flush=True)
        return None, []
    
    # Look for game iframe or embed
    soup = BeautifulSoup(content, 'html.parser')
    game_urls = []
    
    # Method 1: Find iframe
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        iframe_src = iframe.get('src')
        if not iframe_src.startswith('http'):
            iframe_src = urljoin(page_url, iframe_src)
        game_urls.append(iframe_src)
        print(f"    ✓ Found iframe: {iframe_src[:80]}...", flush=True)
    
    # Method 2: Look in scripts for game URLs
    scripts = soup.find_all('script')
    for script in scripts:
        script_content = script.string or ''
        if not script_content:
            continue
        
        # Look for Unity/WebGL game URLs
        unity_urls = re.findall(r'https?://[^"\']+\.(?:data|framework|loader|wasm|br|unity3d)', script_content, re.I)
        game_urls.extend(unity_urls)
        
        # Look for game CDN URLs
        cdn_urls = re.findall(r'https?://[^"\']*(?:cdn|games|y8games)[^"\']*\.(?:js|html|wasm|data)', script_content, re.I)
        game_urls.extend(cdn_urls)
        
        # Look for game ID and construct URL
        game_id_match = re.search(r'game[Ii]d["\']?\s*[:=]\s*["\']?(\d+)', script_content)
        if game_id_match:
            game_id = game_id_match.group(1)
            possible_urls = [
                f"https://y8games.com/games/{game_id}",
                f"https://www.y8.com/games/{game_id}",
                f"https://cdn.y8.com/games/{game_id}",
            ]
            game_urls.extend(possible_urls)
    
    # Remove duplicates
    game_urls = list(set(game_urls))
    game_urls = [url for url in game_urls if url and not any(x in url.lower() for x in ['account', 'profile', 'api', 'analytics', 'newrelic'])]
    
    if game_urls:
        print(f"    ✓ Found {len(game_urls)} potential game URL(s)", flush=True)
        return game_urls[0], game_urls
    else:
        # Try embed URL
        path = urlparse(page_url).path
        if '/games/' in path:
            game_slug = path.split('/games/')[-1]
            embed_url = f"https://www.y8.com/embed/{game_slug}"
            print(f"    ⚠ Trying embed URL: {embed_url}", flush=True)
            return embed_url, [embed_url]
    
    return None, []

def main():
    game_url = "https://www.y8.com/games/escape_tsunami_for_brainrots"
    
    print("Finding and downloading game files from y8.com...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Find game files
    print("\nStep 1: Finding game files...", flush=True)
    game_embed_url, all_urls = find_game_files(game_url)
    
    if not game_embed_url:
        print("  ✗ Could not find game files", flush=True)
        return
    
    print(f"  ✓ Game URL: {game_embed_url}", flush=True)
    
    # Fetch the game page
    print("\nStep 2: Fetching game page...", flush=True)
    try:
        r = requests.get(game_embed_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        game_html = r.text
        print(f"  ✓ Fetched {len(game_html):,} bytes", flush=True)
    except Exception as e:
        print(f"  ✗ Error: {e}", flush=True)
        return
    
    # Parse and extract game files
    print("\nStep 3: Extracting game assets...", flush=True)
    soup = BeautifulSoup(game_html, 'html.parser')
    
    # Find all game-related files
    game_files = []
    
    # CSS files
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href and not href.startswith('data:'):
            game_files.append(('css', urljoin(game_embed_url, href), link))
    
    # JavaScript files
    for script in soup.find_all('script', src=True):
        src = script.get('src')
        if src and not src.startswith('data:'):
            game_files.append(('js', urljoin(game_embed_url, src), script))
    
    # Images
    for img in soup.find_all('img', src=True):
        src = img.get('src')
        if src and not src.startswith('data:'):
            game_files.append(('img', urljoin(game_embed_url, src), img))
    
    # Look for Unity/WebGL files in scripts
    for script in soup.find_all('script'):
        if script.string:
            # Unity build files
            unity_files = re.findall(r'https?://[^"\']+\.(?:data|framework|loader|wasm|br|unity3d)', script.string, re.I)
            for url in unity_files:
                if url not in [f[1] for f in game_files]:
                    game_files.append(('unity', url, None))
            
            # Other asset files
            asset_files = re.findall(r'https?://[^"\']+\.(?:json|bin|png|jpg|jpeg|webp)', script.string, re.I)
            for url in asset_files:
                if url not in [f[1] for f in game_files]:
                    file_type = 'img' if url.endswith(('.png', '.jpg', '.jpeg', '.webp')) else 'other'
                    game_files.append((file_type, url, None))
    
    # Filter out Y8 wrapper files
    game_files = [f for f in game_files if not any(x in f[1].lower() for x in ['y8.com', 'newrelic', 'analytics', 'account', 'profile'])]
    
    print(f"  ✓ Found {len(game_files)} game files", flush=True)
    
    # Create directory
    game_directory = "escape-tsunami-for-brainrots"
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    # Download files with progress
    print(f"\nStep 4: Downloading game files ({len(game_files)} files)...", flush=True)
    downloaded_files = []
    
    for idx, (file_type, file_url, element) in enumerate(game_files, 1):
        filename = Path(urlparse(file_url).path).name
        if '?' in filename:
            filename = filename.split('?')[0]
        if not filename or filename == '/':
            filename = f"file_{idx}.{file_type}"
        
        filepath = game_path / filename
        
        if download_file(file_url, filepath, show_progress=True, current=idx, total=len(game_files)):
            downloaded_files.append((file_type, filename, element))
            if element:
                if file_type == 'css':
                    element['href'] = filename
                elif file_type == 'js':
                    element['src'] = filename
                elif file_type == 'img':
                    element['src'] = filename
    
    # Update HTML
    base_tag = soup.find('base')
    if not base_tag:
        base_tag = soup.new_tag('base', href='./')
        if soup.head:
            soup.head.insert(0, base_tag)
    else:
        base_tag['href'] = './'
    
    # Save HTML
    print("\nStep 5: Saving game HTML...", flush=True)
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
    print(f"Game: Escape Tsunami for Brainrots", flush=True)
    print(f"Directory: {game_directory}", flush=True)
    print(f"Files downloaded: {len(downloaded_files)}", flush=True)
    print(f"  - CSS: {len([f for f in downloaded_files if f[0] == 'css'])}", flush=True)
    print(f"  - JavaScript: {len([f for f in downloaded_files if f[0] == 'js'])}", flush=True)
    print(f"  - Images: {len([f for f in downloaded_files if f[0] == 'img'])}", flush=True)
    print(f"  - Unity/Other: {len([f for f in downloaded_files if f[0] in ['unity', 'other']])}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

