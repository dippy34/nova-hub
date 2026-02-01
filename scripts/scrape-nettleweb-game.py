#!/usr/bin/env python3
"""
Scrape a game from nettleweb.com
"""
import requests
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

def sanitize_filename(name):
    """Convert name to safe directory name"""
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')

def download_file(url, filepath):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"      Error downloading {url}: {e}", flush=True)
        return False

def extract_game_info(html_content, base_url):
    """Extract game information from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to find title
    title = None
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()
    
    # Try to find meta title
    meta_title = soup.find('meta', property='og:title')
    if meta_title and meta_title.get('content'):
        title = meta_title.get('content').strip()
    
    # Try to find game name in h1 or other headings
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
    
    # Try to find cover image
    cover_url = None
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        cover_url = og_image.get('content')
    
    # Try to find favicon or other images
    if not cover_url:
        img = soup.find('img')
        if img and img.get('src'):
            cover_url = urljoin(base_url, img.get('src'))
    
    return title, cover_url

def main():
    game_url = "https://nettleweb.com/ltntrjo7"
    
    print("Scraping game from nettleweb.com...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Fetch the page
    print("\nFetching page...", flush=True)
    try:
        r = requests.get(game_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html_content = r.text
        print(f"✓ Fetched {len(html_content)} bytes", flush=True)
    except Exception as e:
        print(f"✗ Error fetching page: {e}", flush=True)
        return
    
    # Extract game info
    print("\nExtracting game information...", flush=True)
    title, cover_url = extract_game_info(html_content, game_url)
    
    if not title:
        # Try to extract from URL or use default
        title = "Nettleweb Game"
        print("  ⚠ Could not find title, using default", flush=True)
    else:
        print(f"  ✓ Title: {title}", flush=True)
    
    # Create directory name
    dir_name = sanitize_filename(title)
    if not dir_name:
        dir_name = "nettleweb-game"
    
    game_dir = GAMES_DIR / dir_name
    print(f"  ✓ Directory: {dir_name}", flush=True)
    
    # Download HTML
    print(f"\nDownloading game files...", flush=True)
    html_file = game_dir / "index.html"
    print(f"  Downloading HTML...", flush=True)
    if download_file(game_url, html_file):
        print(f"    ✓ Saved to {html_file}", flush=True)
    else:
        print(f"    ✗ Failed to download HTML", flush=True)
        return
    
    # Download cover image if found
    if cover_url:
        print(f"  Downloading cover image...", flush=True)
        cover_file = game_dir / "cover.png"
        if download_file(cover_url, cover_file):
            print(f"    ✓ Saved cover image", flush=True)
        else:
            print(f"    ⚠ Could not download cover image", flush=True)
    
    # Add to games.json
    print(f"\nAdding to games.json...", flush=True)
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    # Check if already exists
    existing = False
    for game in games:
        if game.get('directory') == dir_name:
            existing = True
            print(f"  ⚠ Game already exists, updating...", flush=True)
            game['name'] = title
            game['directory'] = dir_name
            game['image'] = 'cover.png' if cover_url else 'image.png'
            game['source'] = 'non-semag'
            if cover_url:
                game['imagePath'] = cover_url
            break
    
    if not existing:
        game_info = {
            'name': title,
            'directory': dir_name,
            'image': 'cover.png' if cover_url else 'image.png',
            'source': 'non-semag'
        }
        if cover_url:
            game_info['imagePath'] = cover_url
        games.append(game_info)
        print(f"  ✓ Added new game entry", flush=True)
    
    # Save games.json
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("SCRAPE COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: {title}", flush=True)
    print(f"Directory: {dir_name}", flush=True)
    print(f"Total games: {len(games)}", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

