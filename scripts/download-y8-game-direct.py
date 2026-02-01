#!/usr/bin/env python3
"""
Download Y8 game files directly from CDN
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
    'Referer': 'https://www.y8.com/',
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
    game_url = "https://www.y8.com/games/escape_tsunami_for_brainrots"
    
    print("Downloading Y8 game files...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Try to find game ID or CDN URL
    print("\nStep 1: Finding game information...", flush=True)
    try:
        r = requests.get(game_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        content = r.text
        print(f"  ✓ Fetched {len(content):,} bytes", flush=True)
    except Exception as e:
        print(f"  ✗ Error: {e}", flush=True)
        return
    
    # Try common Y8 game CDN patterns
    # Y8 games are often hosted on y8games.com or cdn.y8.com
    game_slug = "escape_tsunami_for_brainrots"
    
    # Common Y8 game URL patterns
    possible_game_urls = [
        f"https://y8games.com/games/{game_slug}",
        f"https://www.y8games.com/games/{game_slug}",
        f"https://cdn.y8.com/games/{game_slug}",
        f"https://games.y8.com/{game_slug}",
    ]
    
    game_html = None
    game_base_url = None
    
    print("  Trying game CDN URLs...", flush=True)
    for url in possible_game_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 1000:  # Valid HTML
                game_html = r.text
                game_base_url = url
                print(f"    ✓ Found game at: {url}", flush=True)
                break
        except:
            continue
    
    if not game_html:
        # Try embed URL
        embed_url = f"https://www.y8.com/embed/{game_slug}"
        print(f"  Trying embed URL: {embed_url}", flush=True)
        try:
            r = requests.get(embed_url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                game_html = r.text
                game_base_url = embed_url
                print(f"    ✓ Using embed URL", flush=True)
        except Exception as e:
            print(f"    ✗ Error: {e}", flush=True)
    
    if not game_html:
        print("  ✗ Could not find game files", flush=True)
        print("  ⚠ Y8 games load dynamically. Creating iframe wrapper instead.", flush=True)
        
        # Create simple iframe wrapper
        game_directory = "escape-tsunami-for-brainrots"
        game_path = GAMES_DIR / game_directory
        game_path.mkdir(parents=True, exist_ok=True)
        
        iframe_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Escape Tsunami for Brainrots</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <iframe src="https://www.y8.com/embed/{game_slug}" allowfullscreen></iframe>
</body>
</html>"""
        
        with open(game_path / "index.html", 'w', encoding='utf-8') as f:
            f.write(iframe_html)
        
        print(f"  ✓ Created iframe wrapper", flush=True)
        return
    
    # Parse game HTML and find assets
    print("\nStep 2: Extracting game assets...", flush=True)
    soup = BeautifulSoup(game_html, 'html.parser')
    
    game_files = []
    
    # Find CSS
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href and not href.startswith('data:'):
            game_files.append(('css', urljoin(game_base_url, href), link))
    
    # Find JavaScript
    for script in soup.find_all('script', src=True):
        src = script.get('src')
        if src and not src.startswith('data:'):
            game_files.append(('js', urljoin(game_base_url, src), script))
    
    # Find images
    for img in soup.find_all('img', src=True):
        src = img.get('src')
        if src and not src.startswith('data:'):
            game_files.append(('img', urljoin(game_base_url, src), img))
    
    # Find Unity/WebGL files in script content
    for script in soup.find_all('script'):
        if script.string:
            # Unity build files
            unity_pattern = r'https?://[^"\']+\.(?:data|framework|loader|wasm|br|unity3d)'
            unity_files = re.findall(unity_pattern, script.string, re.I)
            for url in unity_files:
                if url not in [f[1] for f in game_files]:
                    game_files.append(('unity', url, None))
            
            # Other assets
            asset_pattern = r'https?://[^"\']+\.(?:json|bin|png|jpg|jpeg|webp|svg)'
            asset_files = re.findall(asset_pattern, script.string, re.I)
            for url in asset_files:
                if url not in [f[1] for f in game_files]:
                    file_type = 'img' if any(url.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.svg']) else 'other'
                    game_files.append((file_type, url, None))
    
    # Filter out non-game files
    game_files = [f for f in game_files if not any(x in f[1].lower() for x in ['newrelic', 'analytics', 'account', 'profile', 'privacy'])]
    
    print(f"  ✓ Found {len(game_files)} game files", flush=True)
    
    # Create directory
    game_directory = "escape-tsunami-for-brainrots"
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    # Download files
    print(f"\nStep 3: Downloading game files ({len(game_files)} files)...", flush=True)
    downloaded = []
    
    for idx, (file_type, file_url, element) in enumerate(game_files, 1):
        filename = Path(urlparse(file_url).path).name
        if '?' in filename:
            filename = filename.split('?')[0]
        if not filename or filename == '/':
            ext = {'css': 'css', 'js': 'js', 'img': 'png', 'unity': 'wasm', 'other': 'bin'}.get(file_type, 'bin')
            filename = f"file_{idx}.{ext}"
        
        filepath = game_path / filename
        
        if download_file(file_url, filepath, show_progress=True, current=idx, total=len(game_files)):
            downloaded.append((file_type, filename, element))
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
    print("\nStep 4: Saving game HTML...", flush=True)
    html_file = game_path / "index.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"  ✓ Saved index.html", flush=True)
    
    # Download cover
    print("\nStep 5: Downloading cover...", flush=True)
    og_image = soup.find('meta', property='og:image')
    if og_image:
        cover_url = og_image.get('content', '')
        if cover_url:
            cover_file = game_path / "cover.png"
            if download_file(cover_url, cover_file):
                print("  ✓ Saved cover.png", flush=True)
    
    # Update games.json
    print("\nStep 6: Updating games.json...", flush=True)
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
    main()

