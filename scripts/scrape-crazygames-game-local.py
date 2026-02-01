#!/usr/bin/env python3
"""
Scrape game from CrazyGames and download locally (like Stickman Destruction)
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
    
    print("Scraping Deadly Descent from CrazyGames (local download)...")
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
        print("\nStep 2: Finding game embed URL...", flush=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract game name
        title_tag = soup.find('title')
        if title_tag and 'Deadly Descent' in title_tag.text:
            game_name = "Deadly Descent"
            print(f"  ✓ Game name: {game_name}", flush=True)
        
        # Find the actual game URL from the page
        game_embed_url = None
        
        # Look in script tags for game URLs
        for script in soup.find_all('script'):
            if script.string:
                # Look for game file URLs
                patterns = [
                    r'https://[^"\']*deadly-descent[^"\']*\.(crazygames|game-files)[^"\']*',
                    r'https://[^"\']*game-files\.crazygames\.com[^"\']*deadly-descent[^"\']*',
                    r'["\']([^"\']*deadly-descent[^"\']*index\.html[^"\']*)["\']',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, script.string, re.I)
                    for match in matches:
                        if isinstance(match, tuple):
                            url = match[0] if match[0] else match[1] if len(match) > 1 else ''
                        else:
                            url = match
                        if url and 'deadly-descent' in url.lower():
                            game_embed_url = url
                            break
                    if game_embed_url:
                        break
        
        # If not found in scripts, try the URL we found earlier
        if not game_embed_url:
            game_embed_url = "https://deadly-descent-bzs.game-files.crazygames.com/deadly-descent-bzs/133/index.html"
            print(f"  ✓ Using known game URL: {game_embed_url[:80]}", flush=True)
        else:
            print(f"  ✓ Found game URL: {game_embed_url[:80]}", flush=True)
        
        # Fetch the game page
        print("\nStep 3: Fetching game page...", flush=True)
        try:
            game_response = requests.get(game_embed_url, headers={**HEADERS, 'Referer': game_url}, timeout=30)
            if game_response.status_code == 200:
                print(f"  ✓ Game page fetched (Status: {game_response.status_code})", flush=True)
                game_html = game_response.text
            else:
                print(f"  ⚠ Game page returned {game_response.status_code}, will use base href method", flush=True)
                game_html = None
        except Exception as e:
            print(f"  ⚠ Could not fetch game page: {e}, will use base href method", flush=True)
            game_html = None
        
        # Download cover image
        print("\nStep 4: Downloading cover image...", flush=True)
        cover_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
        
        if cover_url:
            cover_url = urljoin(game_url, cover_url)
            cover_file = game_path / "cover.png"
            if download_file(cover_url, cover_file):
                print("  ✓ Saved cover.png", flush=True)
            else:
                print("  ⚠ Could not download cover image", flush=True)
        else:
            print("  ⚠ No cover image found", flush=True)
        
        # Create HTML wrapper (similar to Stickman Destruction)
        print("\nStep 5: Creating HTML wrapper...", flush=True)
        
        # Extract base URL from game embed URL
        parsed_url = urlparse(game_embed_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en-us">
<head>
  <meta charset="utf-8">
  <base href="{base_url}">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>{game_name}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style type="text/css">
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #000;
    }}
  </style>
</head>
<body>
  <iframe id="game-iframe" src="{game_embed_url}" style="width: 100%; height: 100%; border: none;" allowfullscreen webkitallowfullscreen mozallowfullscreen allow="fullscreen; autoplay; encrypted-media" playsinline webkit-playsinline></iframe>
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
    print(f"Note: Game loads from CDN using base href (like Stickman Destruction)", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

