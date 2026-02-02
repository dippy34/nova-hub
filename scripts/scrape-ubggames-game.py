#!/usr/bin/env python3
"""
Scrape a game from ubggames.com
"""
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
import time

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://ubggames.com/',
}

def sanitize_filename(name):
    """Sanitize filename"""
    return re.sub(r'[^\w\-_\.]', '_', name).lower()

def download_file(url, filepath, show_progress=False):
    """Download a file"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if show_progress:
            size_mb = filepath.stat().st_size / 1024 / 1024
            print(f"    Downloaded: {filepath.name} ({size_mb:.2f} MB)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"    Failed to download {filepath.name}: {e}", flush=True)
        return False

def get_existing_games():
    """Get set of existing game directories, URLs, and names"""
    existing_dirs = set()
    existing_urls = set()
    existing_names = set()
    
    if GAMES_JSON_PATH.exists():
        with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        games = data if isinstance(data, list) else data.get('games', [])
        
        for g in games:
            dir_name = g.get('directory', '').lower()
            if dir_name:
                existing_dirs.add(dir_name)
            
            url = g.get('url', '')
            if url:
                existing_urls.add(url.lower())
            
            name = g.get('name', '').lower()
            if name:
                existing_names.add(name)
                existing_names.add(sanitize_filename(name))
    
    return existing_dirs, existing_urls, existing_names

def find_game_iframe_url(soup, base_url):
    """Find the game iframe URL"""
    # Look for iframe tags
    for iframe in soup.find_all('iframe', src=True):
        src = iframe.get('src', '')
        if src:
            full_url = urljoin(base_url, src)
            return full_url
    
    # Look in script tags for game URLs
    for script in soup.find_all('script'):
        if script.string:
            # Look for common patterns
            patterns = [
                r'["\']([^"\']*\.html[^"\']*)["\']',
                r'iframe.*src["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'gameUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script.string, re.I)
                for match in matches:
                    if isinstance(match, tuple):
                        url = match[0] if match[0] else ''
                    else:
                        url = match
                    if url and ('game' in url.lower() or '.html' in url.lower()):
                        full_url = urljoin(base_url, url)
                        return full_url
    
    return None

def scrape_ubggames_game(game_url):
    """Scrape a single game from ubggames.com"""
    print(f"Scraping game from: {game_url}")
    print("=" * 60, flush=True)
    
    try:
        # Get existing games
        existing_dirs, existing_urls, existing_names = get_existing_games()
        
        # Fetch the game page
        print("Step 1: Fetching game page...", flush=True)
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract game name
        print("Step 2: Extracting game information...", flush=True)
        title_tag = soup.find('title')
        game_name = "Unknown Game"
        if title_tag:
            game_name = title_tag.text.replace(' - UBGGAMES.com', '').replace(' | UBGGAMES.com', '').strip()
        
        # Try h1
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.text.strip():
            game_name = h1_tag.text.strip()
        
        # Try meta og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            game_name = og_title.get('content').strip()
        
        # Clean up game name
        game_name = re.sub(r'[\U0001F000-\U0001F9FF\U0001FA00-\U0001FAFF]', '', game_name)
        game_name = re.sub(r'[\ufe00-\ufe0f]', '', game_name)
        # Remove site name suffixes
        game_name = re.sub(r'\s*#\s*UBGGAMES\.com.*$', '', game_name, flags=re.I)
        game_name = re.sub(r'\s*-\s*UBGGAMES\.com.*$', '', game_name, flags=re.I)
        game_name = re.sub(r'\s*\|\s*UBGGAMES\.com.*$', '', game_name, flags=re.I)
        game_name = game_name.strip()
        
        if not game_name or game_name == "Unknown Game":
            print("  [FAIL] Could not extract game name", flush=True)
            return False
        
        print(f"  Game Name: {game_name}", flush=True)
        
        # Check for duplicates
        game_name_lower = game_name.lower()
        game_name_sanitized = sanitize_filename(game_name)
        
        if game_name_lower in existing_names or game_name_sanitized in existing_names:
            print(f"  [SKIP] Game already exists: {game_name}", flush=True)
            return False
        
        game_directory = sanitize_filename(game_name)
        if game_directory.lower() in existing_dirs:
            print(f"  [SKIP] Directory already exists: {game_directory}", flush=True)
            return False
        
        # Create directory
        game_path = GAMES_DIR / game_directory
        game_path.mkdir(parents=True, exist_ok=True)
        
        # Download cover image
        print("Step 3: Downloading cover image...", flush=True)
        cover_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
        
        if not cover_url:
            # Try to find image in page
            for img in soup.find_all('img', src=True):
                src = img.get('src', '')
                if 'doge' in src.lower() or 'save' in src.lower() or 'game' in src.lower():
                    cover_url = src
                    break
        
        cover_file = game_path / "cover.png"
        if cover_url:
            cover_url = urljoin(game_url, cover_url)
            if download_file(cover_url, cover_file, show_progress=True):
                print(f"  [OK] Downloaded cover image", flush=True)
            else:
                print(f"  [WARN] Failed to download cover image", flush=True)
        else:
            print(f"  [WARN] No cover image found", flush=True)
        
        # Create iframe wrapper (since game loads dynamically)
        print("Step 4: Creating local HTML wrapper...", flush=True)
        local_html = f"""<!DOCTYPE html>
<html lang="en-us">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>{game_name}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    html, body {{
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
  <iframe src="{game_url}" allowfullscreen></iframe>
</body>
</html>"""
        
        html_file = game_path / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(local_html)
        
        print(f"  [OK] Created {html_file}", flush=True)
        
        # Update games.json
        print("Step 5: Updating games.json...", flush=True)
        if GAMES_JSON_PATH.exists():
            with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
                games_data = json.load(f)
        else:
            games_data = []
        
        if isinstance(games_data, dict):
            games_list = games_data.get("games", [])
        else:
            games_list = games_data
        
        # Remove existing entry if it exists
        games_list = [g for g in games_list if g.get("directory") != game_directory]
        
        # Add new game
        game_entry = {
            'name': game_name,
            'directory': game_directory,
            'image': 'cover.png' if cover_file.exists() else '',
            'source': 'non-semag',
            'url': f"non-semag/{game_directory}/index.html",
            'is_local': True
        }
        
        games_list.append(game_entry)
        
        if isinstance(games_data, dict):
            games_data["games"] = games_list
        else:
            games_data = games_list
        
        with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(games_data, f, indent='\t', ensure_ascii=False)
        
        print(f"  [OK] Added to games.json", flush=True)
        
        print("\n" + "=" * 60, flush=True)
        print("SCRAPING COMPLETE", flush=True)
        print("=" * 60, flush=True)
        print(f"Game: {game_name}", flush=True)
        print(f"Directory: {game_directory}", flush=True)
        
        return True
        
    except Exception as e:
        import traceback
        print(f"\n[FAIL] Error: {e}", flush=True)
        traceback.print_exc()
        return False

if __name__ == "__main__":
    game_url = "https://ubggames.com/play/save-the-doge"
    scrape_ubggames_game(game_url)

