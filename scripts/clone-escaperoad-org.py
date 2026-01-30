#!/usr/bin/env python3
"""
Remove all Escape Road games and clone them from escaperoad.org
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import sys
import shutil

BASE_URL = "https://escaperoad.org/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"

# Escape Road series game names
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

def remove_escape_road_games():
    """Remove all Escape Road games from games.json and their directories"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    
    with open(games_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    games_to_remove = []
    for game in games:
        name = game.get('name', '').lower()
        if 'escape road' in name:
            games_to_remove.append(game)
            print(f"  Will remove: {game.get('name')} ({game.get('directory')})", flush=True)
    
    # Remove from games list
    for game in games_to_remove:
        games.remove(game)
        
        # Remove directory
        old_dir = GAMES_DIR / game.get('directory', '')
        if old_dir.exists():
            try:
                shutil.rmtree(old_dir)
                print(f"  Removed directory: {game.get('directory')}", flush=True)
            except Exception as e:
                print(f"  Error removing directory {game.get('directory')}: {e}", flush=True)
    
    # Save updated games.json
    with open(games_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print(f"\nRemoved {len(games_to_remove)} Escape Road games", flush=True)
    return games

def find_game_urls(soup, base_url):
    """Find all Escape Road series game URLs from the page"""
    game_urls = {}
    
    # Direct mapping based on the website structure
    url_mapping = {
        "Escape Road": "/escape-road",
        "Escape Road 2": "/escape-road-2",
        "Escape Road City": "/escape-road-city",
        "Escape Road City 2": "/escape-road-city-2",
        "Escape Road Winter": "/escape-road-winter",
        "Escape Road Halloween": "/escape-road-halloween",
    }
    
    # Find links on the page
    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        for game_name, expected_path in url_mapping.items():
            if game_name.lower() in text.lower() or expected_path in href:
                full_url = urljoin(base_url, href if href.startswith('http') else expected_path)
                if game_name not in game_urls:
                    game_urls[game_name] = full_url
                    print(f"  Found: {game_name} -> {game_urls[game_name]}", flush=True)
    
    # Use direct mapping for any missing games
    for game_name, path in url_mapping.items():
        if game_name not in game_urls:
            full_url = urljoin(base_url, path)
            game_urls[game_name] = full_url
            print(f"  Using direct URL: {game_name} -> {full_url}", flush=True)
    
    return game_urls

def download_game_html(game_url, game_dir):
    """Download the game HTML and extract game content"""
    try:
        game_dir.mkdir(parents=True, exist_ok=True)
        
        # Download the game page
        r = requests.get(game_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        html_content = r.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for data-iframe attribute (the actual game URL)
        iframe_url = None
        show_embed = soup.find(id='show-embed')
        if show_embed:
            iframe_url = show_embed.get('data-iframe', '')
            if iframe_url:
                print(f"    Found game iframe URL: {iframe_url}", flush=True)
                
                try:
                    # Download the actual game from 1games.io
                    game_r = requests.get(iframe_url, headers=HEADERS, timeout=15)
                    game_r.raise_for_status()
                    
                    # Save the game HTML
                    html_file = game_dir / "index.html"
                    with open(html_file, 'wb') as f:
                        f.write(game_r.content)
                    
                    print(f"    ✓ Downloaded game from {iframe_url}", flush=True)
                    return True
                except Exception as e:
                    print(f"    Could not download from iframe URL: {e}", flush=True)
        
        # Fallback: Look for iframe src
        iframe = soup.find('iframe', class_='game-iframe')
        if iframe:
            iframe_src = iframe.get('src', '')
            if iframe_src and iframe_src not in ['about:blank', '']:
                iframe_src = urljoin(game_url, iframe_src)
                print(f"    Found iframe src: {iframe_src}", flush=True)
                
                try:
                    iframe_r = requests.get(iframe_src, headers=HEADERS, timeout=15)
                    iframe_r.raise_for_status()
                    
                    html_file = game_dir / "index.html"
                    with open(html_file, 'wb') as f:
                        f.write(iframe_r.content)
                    
                    return True
                except Exception as e:
                    print(f"    Could not download iframe: {e}", flush=True)
        
        # Last resort: save the full page
        html_file = game_dir / "index.html"
        with open(html_file, 'wb') as f:
            f.write(r.content)
        
        print(f"    Saved full page HTML (game may load via JavaScript)", flush=True)
        return True
        
    except Exception as e:
        print(f"    Error downloading game HTML: {e}", flush=True)
        return False

def download_cover_image(game_name, game_dir, game_url):
    """Try to find and download cover image"""
    try:
        r = requests.get(game_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Look for og:image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
            if cover_url:
                cover_url = urljoin(game_url, cover_url)
                cover_file = game_dir / "cover.png"
                if download_file(cover_url, cover_file, silent=True):
                    print(f"    Downloaded cover image", flush=True)
                    return True
        
        # Look for img tags with game name
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            if game_name.lower() in alt or 'cover' in alt or 'logo' in alt:
                if src and not src.startswith('data:'):
                    cover_url = urljoin(game_url, src)
                    cover_file = game_dir / "cover.png"
                    if download_file(cover_url, cover_file, silent=True):
                        print(f"    Downloaded cover image", flush=True)
                        return True
    except:
        pass
    
    print(f"    ⚠ Could not find cover image", flush=True)
    return False

def normalize_directory_name(name):
    """Convert game name to directory name"""
    dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return dir_name

def main():
    print("Escape Road Games Cloner from escaperoad.org")
    print("=" * 60, flush=True)
    
    # Step 1: Remove existing Escape Road games
    print("\nStep 1: Removing existing Escape Road games...", flush=True)
    existing_games = remove_escape_road_games()
    
    # Step 2: Fetch the main page
    print(f"\nStep 2: Fetching {BASE_URL}...", flush=True)
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching page: {e}", flush=True)
        return
    
    # Step 3: Find all Escape Road series game URLs
    print("\nStep 3: Finding Escape Road series games...", flush=True)
    game_urls = find_game_urls(soup, BASE_URL)
    
    if not game_urls:
        print("⚠ No Escape Road series games found!", flush=True)
        return
    
    print(f"\nFound {len(game_urls)} Escape Road series games", flush=True)
    
    # Step 4: Download new games
    print(f"\nStep 4: Downloading {len(game_urls)} Escape Road series games...", flush=True)
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
    
    # Step 5: Add new games to games.json
    if downloaded_games:
        existing_games.extend(downloaded_games)
        games_file = Path(__file__).parent.parent / "data" / "games.json"
        
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n" + "=" * 60, flush=True)
        print(f"DOWNLOAD SUMMARY", flush=True)
        print(f"=" * 60, flush=True)
        print(f"Downloaded new games: {len(downloaded_games)}/{len(game_urls)}", flush=True)
        print(f"✓ Updated games.json", flush=True)
        print(f"✓ Total games in database: {len(existing_games)}", flush=True)
    else:
        print("\n⚠ No games were successfully downloaded", flush=True)

if __name__ == "__main__":
    main()

