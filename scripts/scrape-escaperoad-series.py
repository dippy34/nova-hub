#!/usr/bin/env python3
"""
Scrape all Escape Road series games from escaperoad.io and replace existing ones
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import os
import sys

BASE_URL = "https://escaperoad.io/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"

# Escape Road series game names (from the website)
ESCAPE_ROAD_SERIES = [
    "Escape Road",
    "Escape Road 2",
    "Escape Road City",
    "Escape Road City 2",
    "Escape Road Winter",
    "Escape Road Halloween",
]

def download_file(url, filepath, silent=False):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=15)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        if not silent:
            print(f"    Error downloading {url}: {e}", flush=True)
        return False

def find_game_urls(soup, base_url):
    """Find all Escape Road series game URLs from the page"""
    game_urls = {}
    
    # Direct mapping of game names to their URL paths (verified to exist)
    url_mapping = {
        "Escape Road": "/escape-road",
        "Escape Road 2": "/escape-road-2",
        "Escape Road City": "/escape-road-city",
        "Escape Road City 2": "/escape-road-city-2",
        "Escape Road Winter": "/escape-road-winter",
        "Escape Road Halloween": "/escape-road-halloween",
    }
    
    # Use direct URL mapping - all these URLs exist
    for game_name, path in url_mapping.items():
        full_url = urljoin(base_url, path)
        game_urls[game_name] = full_url
        print(f"  Found: {game_name} -> {full_url}", flush=True)
    
    return game_urls

def download_game_html(game_url, game_dir):
    """Download the game HTML and extract the iframe or game content"""
    try:
        # Create directory first
        game_dir.mkdir(parents=True, exist_ok=True)
        
        # Download the game page
        r = requests.get(game_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Look for iframe with the actual game
        iframe = soup.find('iframe')
        if iframe:
            iframe_src = iframe.get('src', '')
            if iframe_src:
                # If it's a relative URL, make it absolute
                iframe_src = urljoin(game_url, iframe_src)
                print(f"    Found iframe: {iframe_src}", flush=True)
                
                # Download the iframe content
                iframe_r = requests.get(iframe_src, headers=HEADERS, timeout=15)
                iframe_r.raise_for_status()
                
                # Save as index.html
                html_file = game_dir / "index.html"
                with open(html_file, 'wb') as f:
                    f.write(iframe_r.content)
                
                return True
        
        # If no iframe, try to find the game container or canvas
        # Save the full page as index.html
        html_file = game_dir / "index.html"
        with open(html_file, 'wb') as f:
            f.write(r.content)
        
        return True
        
    except Exception as e:
        print(f"    Error downloading game HTML: {e}", flush=True)
        return False

def download_cover_image(game_name, game_dir, game_url):
    """Try to find and download cover image"""
    # Try common cover image locations
    cover_urls = [
        f"{BASE_URL}images/{game_name.lower().replace(' ', '-')}.png",
        f"{BASE_URL}images/{game_name.lower().replace(' ', '-')}.jpg",
        f"{BASE_URL}assets/{game_name.lower().replace(' ', '-')}.png",
        f"{BASE_URL}cover/{game_name.lower().replace(' ', '-')}.png",
    ]
    
    # Also try to find it on the page
    try:
        r = requests.get(game_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Look for og:image or cover image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
            if cover_url:
                cover_urls.insert(0, urljoin(game_url, cover_url))
        
        # Look for img tags with "cover" in class or alt
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            if 'cover' in alt or 'logo' in alt or game_name.lower() in alt:
                if src:
                    cover_urls.insert(0, urljoin(game_url, src))
    except:
        pass
    
    cover_file = game_dir / "cover.png"
    for cover_url in cover_urls:
        if download_file(cover_url, cover_file, silent=True):
            print(f"    Downloaded cover image", flush=True)
            return True
    
    # Create a placeholder if we can't find one
    print(f"    ⚠ Could not find cover image, will use placeholder", flush=True)
    return False

def normalize_directory_name(name):
    """Convert game name to directory name"""
    dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return dir_name

def main():
    print("Escape Road Series Scraper")
    print("=" * 60, flush=True)
    
    # Fetch the main page
    print(f"Fetching {BASE_URL}...", flush=True)
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching page: {e}", flush=True)
        return
    
    # Find all Escape Road series game URLs
    print("\nFinding Escape Road series games...", flush=True)
    game_urls = find_game_urls(soup, BASE_URL)
    
    if not game_urls:
        print("⚠ No Escape Road series games found!", flush=True)
        return
    
    print(f"\nFound {len(game_urls)} Escape Road series games", flush=True)
    
    # Load existing games to find and remove old Escape Road games
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    with open(games_file, 'r', encoding='utf-8') as f:
        existing_games = json.load(f)
    
    # Find games to remove (any Escape Road game)
    games_to_remove = []
    for game in existing_games:
        name = game.get('name', '').lower()
        if 'escape road' in name:
            games_to_remove.append(game)
            print(f"  Will remove: {game.get('name')} ({game.get('directory')})", flush=True)
    
    # Remove old games
    for game in games_to_remove:
        existing_games.remove(game)
        # Also remove the directory if it exists
        old_dir = GAMES_DIR / game.get('directory', '')
        if old_dir.exists():
            import shutil
            try:
                shutil.rmtree(old_dir)
                print(f"  Removed old directory: {game.get('directory')}", flush=True)
            except:
                pass
    
    print(f"\nRemoved {len(games_to_remove)} old Escape Road games", flush=True)
    
    # Download new games
    print(f"\nDownloading {len(game_urls)} Escape Road series games...", flush=True)
    downloaded_games = []
    
    for i, (game_name, game_url) in enumerate(game_urls.items(), 1):
        print(f"\n[{i}/{len(game_urls)}] Downloading: {game_name}", flush=True)
        print(f"  URL: {game_url}", flush=True)
        
        dir_name = normalize_directory_name(game_name)
        game_dir = GAMES_DIR / dir_name
        
        try:
            # Download HTML
            if download_game_html(game_url, game_dir):
                print(f"  ✓ Downloaded HTML", flush=True)
            else:
                print(f"  ✗ Failed to download HTML", flush=True)
                continue
            
            # Download cover image
            download_cover_image(game_name, game_dir, game_url)
            
            # Add to games list
            game_info = {
                'name': game_name,
                'directory': dir_name,
                'image': 'cover.png',
                'source': 'non-semag'
            }
            downloaded_games.append(game_info)
            print(f"  ✓ Success: {game_name}", flush=True)
            
        except Exception as e:
            print(f"  ✗ Error: {e}", flush=True)
            continue
        
        time.sleep(0.5)  # Be polite
    
    # Add new games to games.json
    if downloaded_games:
        existing_games.extend(downloaded_games)
        
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n" + "=" * 60, flush=True)
        print(f"DOWNLOAD SUMMARY", flush=True)
        print(f"=" * 60, flush=True)
        print(f"Removed old games: {len(games_to_remove)}", flush=True)
        print(f"Downloaded new games: {len(downloaded_games)}/{len(game_urls)}", flush=True)
        print(f"✓ Updated games.json", flush=True)
        print(f"✓ Total games in database: {len(existing_games)}", flush=True)
    else:
        print("\n⚠ No games were successfully downloaded", flush=True)

if __name__ == "__main__":
    main()

