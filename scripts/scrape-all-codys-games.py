#!/usr/bin/env python3
"""
Scrape all games from codys-shack-games.pages.dev/projects
Download all files, not iframe, and skip games we already have
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

def scrape_codys_game(game_url, existing_dirs, existing_urls, existing_names):
    """Scrape a single game from codys-shack-games.pages.dev"""
    try:
        # Fetch the game page
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract game name
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
        game_name = re.sub(r'\s*\|\s*3kh0.*$', '', game_name, flags=re.I)
        game_name = re.sub(r'\s*-\s*cody.*shack.*$', '', game_name, flags=re.I)
        game_name = game_name.strip()
        
        if not game_name or game_name == "Unknown Game":
            return None, "Could not extract game name"
        
        # Check for duplicates - normalize name for comparison
        game_name_lower = game_name.lower()
        game_name_sanitized = sanitize_filename(game_name)
        
        # Remove common suffixes for comparison
        game_name_normalized = re.sub(r'\s*\|\s*3kh0.*$', '', game_name_lower, flags=re.I)
        game_name_normalized = re.sub(r'\s*-\s*cody.*shack.*$', '', game_name_normalized, flags=re.I)
        game_name_normalized = re.sub(r'\s+game\s*$', '', game_name_normalized)
        game_name_normalized = game_name_normalized.strip()
        
        # Check exact matches
        if game_name_lower in existing_names or game_name_sanitized in existing_names:
            return None, f"Already exists (name: {game_name})"
        
        # Check normalized matches
        for existing_name in existing_names:
            existing_normalized = re.sub(r'\s*\|\s*3kh0.*$', '', existing_name.lower(), flags=re.I)
            existing_normalized = re.sub(r'\s*-\s*cody.*shack.*$', '', existing_normalized, flags=re.I)
            existing_normalized = re.sub(r'\s+game\s*$', '', existing_normalized)
            existing_normalized = existing_normalized.strip()
            
            if game_name_normalized == existing_normalized and len(game_name_normalized) > 2:
                return None, f"Already exists (similar name: {game_name} vs {existing_name})"
        
        game_directory = sanitize_filename(game_name)
        if game_directory.lower() in existing_dirs:
            return None, f"Already exists (directory: {game_directory})"
        
        # Also check if URL already exists
        game_url_path = f"non-semag/{game_directory}/index.html"
        if game_url_path.lower() in existing_urls:
            return None, f"Already exists (URL: {game_url_path})"
        
        # Create directory
        game_path = GAMES_DIR / game_directory
        game_path.mkdir(parents=True, exist_ok=True)
        
        # Parse base URL
        parsed_url = urlparse(game_url)
        base_domain = parsed_url.netloc
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
        
        def is_same_domain(url):
            """Check if URL is from the same domain"""
            try:
                parsed = urlparse(url)
                return parsed.netloc == base_domain or parsed.netloc == ''
            except:
                return False
        
        # Find all assets to download
        assets_to_download = []
        seen_urls = set()
        
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
        
        # Look for references to files in JavaScript code (like kernel.txt, data files)
        for script in soup.find_all('script'):
            if script.string:
                patterns = [
                    r'["\']([^"\']*\.txt[^"\']*)["\']',
                    r'fetch\(["\']([^"\']+)["\']',
                    r'\.open\(["\']GET["\'],\s*["\']([^"\']+)["\']',
                    r'["\']([^"\']*\.json[^"\']*)["\']',
                    r'["\']([^"\']*\.xml[^"\']*)["\']',
                    r'Typer\.file\s*=\s*["\']([^"\']+)["\']',
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
        
        # Download cover image
        cover_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
        
        if not cover_url:
            for img in soup.find_all('img', src=True):
                src = img.get('src', '')
                if any(x in src.lower() for x in ['logo', 'icon', 'cover', 'thumbnail', 'preview']):
                    cover_url = src
                    break
        
        cover_file = game_path / "cover.png"
        if cover_url:
            cover_url = urljoin(game_url, cover_url)
            download_file(cover_url, cover_file)
        
        # Download favicon if referenced
        favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
        if favicon and favicon.get('href'):
            favicon_url = urljoin(game_url, favicon.get('href'))
            if is_same_domain(favicon_url):
                favicon_file = game_path / "favicon.ico"
                download_file(favicon_url, favicon_file)
        
        # Download all assets
        downloaded_count = 0
        html_content = response.text
        
        for idx, (asset_type, relative_path, full_url) in enumerate(assets_to_download, 1):
            if relative_path.startswith('/'):
                path_parts = relative_path.lstrip('/').split('/')
                sanitized_parts = [sanitize_filename(part) for part in path_parts]
                local_path = game_path / '/'.join(sanitized_parts)
            else:
                path_parts = relative_path.split('/')
                sanitized_parts = [sanitize_filename(part) if part else part for part in path_parts]
                local_path = game_path / '/'.join(sanitized_parts)
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            if download_file(full_url, local_path, show_progress=True, current=idx, total=len(assets_to_download)):
                downloaded_count += 1
                if relative_path.startswith('/'):
                    new_path = '/'.join(sanitized_parts)
                else:
                    new_path = '/'.join(sanitized_parts)
                html_content = html_content.replace(relative_path, new_path)
                html_content = html_content.replace(full_url, new_path)
        
        # Update base tag
        if '<base' in html_content:
            html_content = re.sub(r'<base[^>]*>', f'<base href="./">', html_content)
        else:
            html_content = html_content.replace('<head>', '<head>\n  <base href="./">', 1)
        
        # Save HTML
        html_file = game_path / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            'name': game_name,
            'directory': game_directory,
            'image': 'cover.png' if cover_file.exists() else '',
            'source': 'non-semag',
            'url': f"non-semag/{game_directory}/index.html",
            'is_local': True
        }, "Success"
        
    except Exception as e:
        import traceback
        return None, f"Error: {str(e)[:100]}"

def main():
    print("Scraping all games from codys-shack-games.pages.dev/projects...")
    print("=" * 60, flush=True)
    
    # Get existing games
    existing_dirs, existing_urls, existing_names = get_existing_games()
    print(f"Found {len(existing_dirs)} existing games", flush=True)
    
    # Get game list from GitHub API
    print("\nStep 1: Fetching game list from GitHub API...", flush=True)
    game_urls = []
    
    try:
        api_url = "https://api.github.com/repos/theinfamouscoder5/codys-shack-games/contents/projects"
        response = requests.get(api_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            projects = response.json()
            base_url = "https://codys-shack-games.pages.dev/projects"
            for project in projects:
                if project.get('type') == 'dir':
                    project_name = project.get('name', '')
                    if project_name:
                        game_url = f"{base_url}/{project_name}/"
                        game_urls.append(game_url)
            print(f"  Found {len(game_urls)} projects from GitHub API", flush=True)
        else:
            print(f"  [WARN] GitHub API returned {response.status_code}", flush=True)
    except Exception as e:
        print(f"  [WARN] Could not fetch from GitHub API: {e}", flush=True)
    
    if len(game_urls) == 0:
        print("  [WARN] No games found via GitHub API, trying projects page...", flush=True)
        projects_url = "https://codys-shack-games.pages.dev/projects"
        response = requests.get(projects_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/projects/' in href:
                full_url = urljoin(projects_url, href)
                if full_url not in game_urls and full_url != projects_url:
                    game_urls.append(full_url)
    
    print(f"  Total: {len(game_urls)} game URLs to process", flush=True)
    
    # Scrape games
    print(f"\nStep 2: Scraping games (showing progress)...", flush=True)
    scraped_games = []
    skipped = 0
    failed = 0
    
    for idx, game_url in enumerate(game_urls, 1):
        print(f"\n[{idx}/{len(game_urls)}] Processing: {game_url[:60]}...", flush=True)
        
        game_entry, status = scrape_codys_game(game_url, existing_dirs, existing_urls, existing_names)
        
        if game_entry:
            scraped_games.append(game_entry)
            existing_dirs.add(game_entry['directory'].lower())
            existing_urls.add(game_entry['url'].lower())
            existing_names.add(game_entry['name'].lower())
            existing_names.add(sanitize_filename(game_entry['name']))
            print(f"  [OK] {game_entry['name']} - {status}", flush=True)
            print(f"    Progress: {len(scraped_games)} games scraped", flush=True)
        elif "Already exists" in status:
            skipped += 1
            print(f"  [SKIP] {status}", flush=True)
        else:
            failed += 1
            print(f"  [FAIL] {status}", flush=True)
        
        time.sleep(0.5)  # Small delay to avoid rate limiting
    
    # Update games.json
    if scraped_games:
        print(f"\nStep 3: Updating games.json...", flush=True)
        if GAMES_JSON_PATH.exists():
            with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
                games_data = json.load(f)
        else:
            games_data = []
        
        if isinstance(games_data, dict):
            games_list = games_data.get("games", [])
        else:
            games_list = games_data
        
        # Remove existing entries
        for new_game in scraped_games:
            games_list = [g for g in games_list if g.get("directory") != new_game['directory']]
        
        games_list.extend(scraped_games)
        
        if isinstance(games_data, dict):
            games_data["games"] = games_list
        else:
            games_data = games_list
        
        with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(games_data, f, indent='\t', ensure_ascii=False)
        
        print(f"  [OK] Added {len(scraped_games)} games to games.json", flush=True)
    
    # Summary
    print("\n" + "=" * 60, flush=True)
    print("SCRAPING COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Successfully scraped: {len(scraped_games)} games", flush=True)
    print(f"Skipped (already exist): {skipped} games", flush=True)
    print(f"Failed: {failed} games", flush=True)
    print(f"Total processed: {len(game_urls)} URLs", flush=True)
    
    if scraped_games:
        print(f"\nScraped games:", flush=True)
        for game in scraped_games:
            print(f"  - {game['name']}", flush=True)

if __name__ == "__main__":
    main()

