#!/usr/bin/env python3
"""
Scrape Unity WebGL game from shsgames.github.io
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
    game_url = "https://shsgames.github.io/g/4ead5539/kill-the-spartan"
    game_name = "Kill the Spartan"
    game_directory = sanitize_filename("kill-the-spartan")
    
    # The actual game file URL (found via browser network inspection)
    swf_url = "https://cdn.jsdelivr.net/gh/JoshMerlino/shsg-pfile/games/kill-the-spartan.swf"
    
    print("Scraping Kill the Spartan from shsgames.github.io...")
    print("=" * 60, flush=True)
    print(f"Game URL: {game_url}", flush=True)
    print(f"SWF URL: {swf_url}", flush=True)
    
    # Create directory
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download the SWF file
        print("\nStep 1: Downloading SWF file...", flush=True)
        swf_file = game_path / "kill-the-spartan.swf"
        if download_file(swf_url, swf_file, show_progress=True, current=1, total=1):
            print(f"  ✓ Downloaded {swf_file.name}", flush=True)
        else:
            print("  ✗ Failed to download SWF file", flush=True)
            return
        
        # Download cover image
        print("\nStep 2: Downloading cover image...", flush=True)
        # Try to get cover from the game page
        try:
            response = requests.get(game_url, headers=HEADERS, timeout=30, allow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract game name from title if available
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.text.strip()
                    if title_text and title_text != 'Untitled':
                        game_name = title_text.replace(' - shsgames.github.io', '').replace(' - SHS Games', '').replace(' • SHS Games', '').strip()
                        print(f"  ✓ Game name: {game_name}", flush=True)
        except:
            pass
        
        # Try to download cover image
        cover_url = None
        try:
            response = requests.get(game_url, headers=HEADERS, timeout=30, allow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    cover_url = og_image.get('content', '')
                    if cover_url:
                        cover_url = urljoin(game_url, cover_url)
        except:
            pass
        
        if cover_url:
            cover_file = game_path / "cover.png"
            if download_file(cover_url, cover_file):
                print("  ✓ Saved cover.png", flush=True)
            else:
                print("  ⚠ Could not download cover image", flush=True)
        else:
            print("  ⚠ No cover image found, using placeholder", flush=True)
        
        # Create HTML wrapper with Ruffle
        print("\nStep 3: Creating HTML wrapper with Ruffle...", flush=True)
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
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        #game-container {{
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        ruffle-player {{
            width: 100%;
            height: 100%;
        }}
    </style>
</head>
<body>
    <div id="game-container">
        <ruffle-player></ruffle-player>
    </div>
    <script src="https://unpkg.com/@ruffle-rs/ruffle"></script>
    <script>
        window.RufflePlayer = window.RufflePlayer || {{}};
        window.RufflePlayer.config = {{
            "publicPath": "https://unpkg.com/@ruffle-rs/ruffle/",
            "polyfills": true,
        }};
        
        const ruffle = window.RufflePlayer.newest();
        const player = ruffle.createPlayer();
        const container = document.getElementById("game-container");
        container.appendChild(player);
        
        player.load("kill-the-spartan.swf").then(() => {{
            console.log("Game loaded successfully");
        }}).catch((error) => {{
            console.error("Error loading game:", error);
        }});
    </script>
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
    print(f"Files downloaded: SWF file", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

