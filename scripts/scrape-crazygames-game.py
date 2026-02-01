#!/usr/bin/env python3
"""
Scrape game from CrazyGames
"""
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
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
    game_url = "https://www.crazygames.com/game/deadly-descent-bzs"
    game_name = "Deadly Descent"
    game_directory = sanitize_filename("deadly-descent")
    
    print("Scraping Deadly Descent from CrazyGames...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Create directory
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Fetch the page
        print("\nStep 1: Fetching game page...", flush=True)
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        print(f"  ✓ Page fetched (Status: {response.status_code})", flush=True)
        
        # Parse HTML
        print("\nStep 2: Parsing HTML...", flush=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract game name from title if available
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            if title_text and 'Deadly Descent' in title_text:
                game_name = "Deadly Descent"
                print(f"  ✓ Game name: {game_name}", flush=True)
        
        # Find game iframe or embed
        print("\nStep 3: Finding game embed...", flush=True)
        game_iframe = soup.find('iframe', {'id': 'game-iframe'}) or soup.find('iframe', class_=re.compile('game'))
        if not game_iframe:
            # Try to find any iframe
            game_iframe = soup.find('iframe')
        
        if game_iframe:
            iframe_src = game_iframe.get('src', '')
            print(f"  ✓ Found iframe: {iframe_src[:80]}", flush=True)
            
            # If it's a relative URL, make it absolute
            if iframe_src and not iframe_src.startswith('http'):
                iframe_src = urljoin(game_url, iframe_src)
            
            # Download cover image
            print("\nStep 4: Downloading cover image...", flush=True)
            cover_url = None
            
            # Try og:image
            og_image = soup.find('meta', property='og:image')
            if og_image:
                cover_url = og_image.get('content', '')
            
            # Try other image sources
            if not cover_url:
                img_tag = soup.find('img', class_=re.compile('game|cover|thumbnail', re.I))
                if img_tag:
                    cover_url = img_tag.get('src', '')
            
            if cover_url:
                cover_url = urljoin(game_url, cover_url)
                cover_file = game_path / "cover.png"
                if download_file(cover_url, cover_file):
                    print("  ✓ Saved cover.png", flush=True)
                else:
                    print("  ⚠ Could not download cover image", flush=True)
            else:
                print("  ⚠ No cover image found", flush=True)
            
            # Create HTML wrapper
            print("\nStep 5: Creating HTML wrapper...", flush=True)
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
        #game-container {{
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        #game-iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <div id="game-container">
        <iframe id="game-iframe" src="{iframe_src}" allowfullscreen webkitallowfullscreen mozallowfullscreen allow="fullscreen; autoplay; encrypted-media" playsinline webkit-playsinline></iframe>
    </div>
</body>
</html>"""
            
            html_file = game_path / "index.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"  ✓ Saved index.html", flush=True)
        else:
            print("  ⚠ No game iframe found, creating basic wrapper...", flush=True)
            # Create a basic wrapper that loads the original page
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
        #game-container {{
            width: 100%;
            height: 100%;
        }}
        #game-iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <div id="game-container">
        <iframe id="game-iframe" src="{game_url}" allowfullscreen webkitallowfullscreen mozallowfullscreen allow="fullscreen; autoplay; encrypted-media" playsinline webkit-playsinline></iframe>
    </div>
</body>
</html>"""
            
            html_file = game_path / "index.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"  ✓ Saved index.html (iframe to original page)", flush=True)
            
            # Try to download cover
            og_image = soup.find('meta', property='og:image')
            if og_image:
                cover_url = og_image.get('content', '')
                if cover_url:
                    cover_url = urljoin(game_url, cover_url)
                    cover_file = game_path / "cover.png"
                    download_file(cover_url, cover_file)
        
    except Exception as e:
        print(f"\n✗ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return
    
    # Update games.json
    print("\nStep 6: Updating games.json...", flush=True)
    if GAMES_JSON_PATH.exists():
        with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
            games_data = json.load(f)
    else:
        games_data = []
    
    # Handle both list and dict formats
    if isinstance(games_data, dict):
        games_list = games_data.get("games", [])
    else:
        games_list = games_data
    
    # Remove existing entry if it exists
    games_list = [g for g in games_list if g.get("directory") != game_directory]
    
    # Add new entry
    game_entry = {
        "name": game_name,
        "directory": game_directory,
        "image": "cover.png",
        "source": "non-semag",
        "url": f"non-semag/{game_directory}/index.html",
        "is_local": True
    }
    games_list.append(game_entry)
    
    # Save in the same format as loaded
    if isinstance(games_data, dict):
        games_data["games"] = games_list
    else:
        games_data = games_list
    
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(games_data, f, indent='\t', ensure_ascii=False)
    
    print("  ✓ Updated games.json", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("DOWNLOAD COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: {game_name}", flush=True)
    print(f"Directory: {game_directory}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

