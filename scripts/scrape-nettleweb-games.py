#!/usr/bin/env python3
"""
Scrape 3 games from nettleweb.com
"""
import requests
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
MAX_GAMES = 3
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

def sanitize_filename(name):
    """Convert name to safe directory name"""
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')[:50]  # Limit length

def extract_game_links(html_content, base_url):
    """Extract game links from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    # Find all links that look like game URLs (7+ character paths)
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        # Look for paths like /ltntrjo7 or similar
        if href.startswith('/') and len(href) > 1:
            # Check if it looks like a game ID (alphanumeric, 7+ chars)
            path = href.strip('/')
            if re.match(r'^[a-z0-9]{7,}$', path):
                full_url = urljoin(base_url, href)
                title = a.get_text().strip() or path
                links.append((full_url, title))
    
    # Also search in JavaScript for game URLs
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Find URLs in JavaScript
            url_pattern = r'["\']([^"\']*/(?:game|play|ltntrjo7|/[a-z0-9]{7,})[^"\']*)["\']'
            matches = re.findall(url_pattern, script.string)
            for match in matches:
                if match.startswith('http'):
                    links.append((match, 'Game'))
                elif match.startswith('/'):
                    links.append((urljoin(base_url, match), 'Game'))
    
    # Remove duplicates
    seen = set()
    unique_links = []
    for url, title in links:
        if url not in seen:
            seen.add(url)
            unique_links.append((url, title))
    
    return unique_links

def download_game(url, title, game_dir):
    """Download a single game"""
    print(f"\n  Processing: {title}", flush=True)
    print(f"    URL: {url}", flush=True)
    
    # Fetch the game page
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
    except Exception as e:
        print(f"    ✗ Error fetching: {e}", flush=True)
        return False
    
    # Save HTML
    html_file = game_dir / "index.html"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"    ✓ Saved HTML", flush=True)
    
    # Try to find and download cover image
    soup = BeautifulSoup(html_content, 'html.parser')
    cover_url = None
    
    # Check for og:image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        cover_url = urljoin(url, og_image.get('content'))
    
    # Check for favicon
    if not cover_url:
        favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
        if favicon and favicon.get('href'):
            cover_url = urljoin(url, favicon.get('href'))
    
    if cover_url:
        try:
            cover_file = game_dir / "cover.png"
            r_img = requests.get(cover_url, headers=HEADERS, timeout=10)
            if r_img.status_code == 200:
                # Check if it's actually an image
                if r_img.headers.get('content-type', '').startswith('image/'):
                    with open(cover_file, 'wb') as f:
                        f.write(r_img.content)
                    print(f"    ✓ Saved cover image", flush=True)
        except:
            pass  # Cover image is optional
    
    return True

def main():
    base_url = "https://nettleweb.com"
    
    print("Scraping games from nettleweb.com")
    print("=" * 60, flush=True)
    print(f"Target: {MAX_GAMES} games", flush=True)
    
    # Fetch homepage to find game links
    print(f"\nFetching homepage...", flush=True)
    try:
        r = requests.get(base_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
        print(f"✓ Fetched {len(html_content)} bytes", flush=True)
    except Exception as e:
        print(f"✗ Error: {e}", flush=True)
        return
    
    # Extract game links
    print(f"\nExtracting game links...", flush=True)
    game_links = extract_game_links(html_content, base_url)
    print(f"Found {len(game_links)} potential game links", flush=True)
    
    if not game_links:
        print("\n⚠ No game links found. The site might use JavaScript to load games.", flush=True)
        print("Trying to find games in page content...", flush=True)
        
        # Try to find any URLs that might be games
        url_pattern = r'https?://nettleweb\.com/[a-z0-9]{7,}'
        matches = re.findall(url_pattern, html_content)
        if matches:
            game_links = [(url, 'Game') for url in set(matches)]
            print(f"Found {len(game_links)} URLs in content", flush=True)
    
    if not game_links:
        print("\n✗ Could not find any game links. The site structure may be different.", flush=True)
        return
    
    # Limit to MAX_GAMES
    games_to_download = game_links[:MAX_GAMES]
    print(f"\nDownloading {len(games_to_download)} games...", flush=True)
    
    # Load existing games
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    existing_dirs = {g.get('directory', '') for g in games}
    
    downloaded = []
    for i, (url, title) in enumerate(games_to_download, 1):
        print(f"\n[{i}/{len(games_to_download)}] {title}", flush=True)
        
        # Create directory name from URL or title
        path_part = urlparse(url).path.strip('/')
        if path_part:
            dir_name = sanitize_filename(path_part)
        else:
            dir_name = sanitize_filename(title)
        
        if not dir_name:
            dir_name = f"nettleweb-game-{i}"
        
        # Check if already exists
        if dir_name in existing_dirs:
            print(f"  ⚠ Already exists, skipping", flush=True)
            continue
        
        game_dir = GAMES_DIR / dir_name
        
        if download_game(url, title, game_dir):
            game_info = {
                'name': title if title != 'Game' else f"Nettleweb Game {i}",
                'directory': dir_name,
                'image': 'cover.png',
                'source': 'non-semag'
            }
            downloaded.append(game_info)
            existing_dirs.add(dir_name)
            print(f"  ✓ Success", flush=True)
        
        time.sleep(0.5)  # Be polite
    
    # Add to games.json
    if downloaded:
        games.extend(downloaded)
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent='\t', ensure_ascii=False)
        
        print("\n" + "=" * 60, flush=True)
        print("DOWNLOAD SUMMARY", flush=True)
        print("=" * 60, flush=True)
        print(f"Successfully downloaded: {len(downloaded)}/{len(games_to_download)}", flush=True)
        print(f"Total games: {len(games)}", flush=True)
        print(f"✓ Saved to games.json", flush=True)
    else:
        print("\n⚠ No games were downloaded", flush=True)

if __name__ == "__main__":
    main()

