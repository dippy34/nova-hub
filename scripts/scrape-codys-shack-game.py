#!/usr/bin/env python3
"""
Scrape a game from codys-shack-games.pages.dev - download all files, not iframe
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
            print(f"\r    [{current}/{total}] [OK] {filepath.name[:45]:<45} ({size_mb:.2f} MB)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"\r    [{current}/{total}] [FAIL] {filepath.name[:45]:<45} Error: {str(e)[:30]}", flush=True)
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

def scrape_codys_shack_game(game_url):
    """Scrape a game from codys-shack-games.pages.dev"""
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
            game_name = title_tag.text.strip()
        
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
        
        # Parse base URL
        parsed_url = urlparse(game_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
        
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
                if any(x in src.lower() for x in ['logo', 'icon', 'cover', 'thumbnail', 'preview']):
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
        
        # Find all assets to download
        print("Step 4: Finding game assets...", flush=True)
        assets_to_download = []
        seen_urls = set()
        base_domain = parsed_url.netloc
        
        def is_same_domain(url):
            """Check if URL is from the same domain"""
            try:
                parsed = urlparse(url)
                return parsed.netloc == base_domain or parsed.netloc == ''
            except:
                return False
        
        # Find CSS files
        for link in soup.find_all('link', rel='stylesheet', href=True):
            href = link.get('href', '')
            if href and href not in seen_urls:
                full_url = urljoin(game_url, href)
                if is_same_domain(full_url):
                    assets_to_download.append(('css', href, full_url))
                    seen_urls.add(href)
        
        # Find JS files
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if src and src not in seen_urls:
                full_url = urljoin(game_url, src)
                if is_same_domain(full_url):
                    assets_to_download.append(('js', src, full_url))
                    seen_urls.add(src)
        
        # Find images
        for img in soup.find_all('img', src=True):
            src = img.get('src', '')
            if src and src not in seen_urls and not src.startswith('data:'):
                full_url = urljoin(game_url, src)
                if is_same_domain(full_url):
                    assets_to_download.append(('img', src, full_url))
                    seen_urls.add(src)
        
        # Find other resources (fonts, etc.) - only same domain
        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            rel = link.get('rel', [])
            if href and href not in seen_urls and any(r in ['preload', 'prefetch', 'stylesheet'] for r in rel):
                full_url = urljoin(game_url, href)
                if is_same_domain(full_url):
                    assets_to_download.append(('other', href, full_url))
                    seen_urls.add(href)
        
        # Look for references to files in JavaScript code (like kernel.txt)
        for script in soup.find_all('script'):
            if script.string:
                # Find fetch() calls, XMLHttpRequest, or file references
                patterns = [
                    r'["\']([^"\']*\.txt[^"\']*)["\']',
                    r'fetch\(["\']([^"\']+)["\']',
                    r'\.open\(["\']GET["\'],\s*["\']([^"\']+)["\']',
                    r'["\']([^"\']*\.json[^"\']*)["\']',
                    r'["\']([^"\']*\.xml[^"\']*)["\']',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, script.string, re.I)
                    for match in matches:
                        if isinstance(match, tuple):
                            file_path = match[0] if match[0] else ''
                        else:
                            file_path = match
                        if file_path and file_path not in seen_urls and not file_path.startswith('http'):
                            full_url = urljoin(game_url, file_path)
                            if is_same_domain(full_url):
                                assets_to_download.append(('data', file_path, full_url))
                                seen_urls.add(file_path)
        
        print(f"  Found {len(assets_to_download)} assets to download", flush=True)
        
        # Download all assets
        print("Step 5: Downloading game assets...", flush=True)
        downloaded_count = 0
        html_content = response.text
        
        for idx, (asset_type, relative_path, full_url) in enumerate(assets_to_download, 1):
            # Determine local path - sanitize to avoid invalid characters
            if relative_path.startswith('/'):
                # Absolute path - keep structure but sanitize
                path_parts = relative_path.lstrip('/').split('/')
                sanitized_parts = [sanitize_filename(part) for part in path_parts]
                local_path = game_path / '/'.join(sanitized_parts)
            else:
                # Relative path - sanitize filename
                path_parts = relative_path.split('/')
                sanitized_parts = [sanitize_filename(part) if part else part for part in path_parts]
                local_path = game_path / '/'.join(sanitized_parts)
            
            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            if download_file(full_url, local_path, show_progress=True, current=idx, total=len(assets_to_download)):
                downloaded_count += 1
                # Update HTML to use relative path
                if relative_path.startswith('/'):
                    new_path = '/'.join(sanitized_parts)
                else:
                    new_path = '/'.join(sanitized_parts)
                html_content = html_content.replace(relative_path, new_path)
                html_content = html_content.replace(full_url, new_path)
        
        print(f"  [OK] Downloaded {downloaded_count}/{len(assets_to_download)} assets", flush=True)
        
        # Create local HTML file
        print("Step 6: Creating local HTML file...", flush=True)
        # Update base tag if present, or add one
        if '<base' in html_content:
            html_content = re.sub(r'<base[^>]*>', f'<base href="./">', html_content)
        else:
            html_content = html_content.replace('<head>', '<head>\n  <base href="./">', 1)
        
        html_file = game_path / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  [OK] Created {html_file}", flush=True)
        
        # Update games.json
        print("Step 7: Updating games.json...", flush=True)
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
        print(f"Assets downloaded: {downloaded_count}", flush=True)
        
        return True
        
    except Exception as e:
        import traceback
        print(f"\n[FAIL] Error: {e}", flush=True)
        traceback.print_exc()
        return False

if __name__ == "__main__":
    game_url = "https://codys-shack-games.pages.dev/projects/hackertype/"
    scrape_codys_shack_game(game_url)

