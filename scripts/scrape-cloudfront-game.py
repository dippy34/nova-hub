#!/usr/bin/env python3
"""
Scrape game from CloudFront URL
"""
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
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
    game_url = "https://d3rtzzzsiu7gdr.cloudfront.net/play/index.html?Level%20Devil"
    # Extract game name from URL parameter
    parsed_url = urlparse(game_url)
    query_params = parsed_url.query
    if query_params:
        game_name = unquote(query_params).strip()
    else:
        game_name = "Level Devil"
    game_directory = sanitize_filename(game_name)
    
    print("Scraping Level Devil from CloudFront...")
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
            if title_text and title_text != 'Untitled':
                game_name = title_text.replace(' - CloudFront', '').strip()
                print(f"  ✓ Game name: {game_name}", flush=True)
        
        # Find game files
        print("\nStep 3: Finding game files...", flush=True)
        game_files = []
        seen_urls = set()
        
        # Find script tags
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if src:
                full_url = urljoin(game_url, src)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    game_files.append(full_url)
        
        # Find link tags (CSS, etc.)
        for link in soup.find_all('link', href=True):
            href = link.get('href', '')
            if href:
                full_url = urljoin(game_url, href)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    game_files.append(full_url)
        
        # Search in script content for Unity file references
        for script in soup.find_all('script'):
            if script.string:
                # Look for Unity file patterns in JavaScript
                patterns = [
                    r'["\']([^"\']*\.(loader|framework|wasm|data)\.js[^"\']*)["\']',
                    r'["\']([^"\']*\.(wasm|data|framework)[^"\']*)["\']',
                    r'dataUrl:\s*["\']([^"\']+)["\']',
                    r'frameworkUrl:\s*["\']([^"\']+)["\']',
                    r'codeUrl:\s*["\']([^"\']+)["\']',
                    r'["\']([^"\']*\.(js|wasm|data|css|png|jpg|json)[^"\']*)["\']',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            file_path = match[0] if match[0] else match[1] if len(match) > 1 else ''
                        else:
                            file_path = match
                        if file_path and not file_path.startswith('http') and not file_path.startswith('//'):
                            full_url = urljoin(game_url, file_path)
                            if full_url not in seen_urls:
                                seen_urls.add(full_url)
                                game_files.append(full_url)
        
        # Remove duplicates
        game_files = list(set(game_files))
        
        print(f"  ✓ Found {len(game_files)} file(s)", flush=True)
        for url in game_files[:10]:  # Show first 10
            print(f"    - {url[:80]}", flush=True)
        
        # Download game files
        print(f"\nStep 4: Downloading game files ({len(game_files)} files)...", flush=True)
        downloaded_files = []
        
        for idx, file_url in enumerate(game_files, 1):
            # Try to get filename from URL
            parsed = urlparse(file_url)
            filename = Path(parsed.path).name
            
            # If no filename, try to determine from content or URL
            if not filename or filename == '/':
                if 'loader' in file_url.lower():
                    filename = 'loader.js'
                elif 'framework' in file_url.lower():
                    filename = 'framework.js'
                elif 'wasm' in file_url.lower():
                    filename = 'code.wasm'
                elif 'data' in file_url.lower():
                    filename = 'data'
                elif file_url.endswith('.js'):
                    filename = 'script.js'
                elif file_url.endswith('.css'):
                    filename = 'style.css'
                else:
                    filename = f"file_{idx}.js"
            
            filepath = game_path / filename
            
            if download_file(file_url, filepath, show_progress=True, current=idx, total=len(game_files)):
                downloaded_files.append(filename)
        
        # Download cover image
        print("\nStep 5: Downloading cover image...", flush=True)
        cover_url = None
        
        # Try og:image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
        
        # Try favicon or other images
        if not cover_url:
            favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            if favicon:
                cover_url = favicon.get('href', '')
        
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
        print("\nStep 6: Creating HTML wrapper...", flush=True)
        
        # Save the original HTML, but update paths to be relative
        html_content = response.text
        
        # Replace absolute URLs with relative paths
        base_url = game_url.rsplit('/', 1)[0] if '/' in game_url else game_url
        for file_url in game_files:
            parsed = urlparse(file_url)
            filename = Path(parsed.path).name
            if filename:
                # Replace the full URL with just the filename
                html_content = html_content.replace(file_url, filename)
                # Also try replacing with path relative to base
                relative_path = file_url.replace(base_url + '/', '')
                if relative_path != file_url:
                    html_content = html_content.replace(file_url, relative_path)
        
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
    print("\nStep 7: Updating games.json...", flush=True)
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
    print(f"Files downloaded: {len(downloaded_files)}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

