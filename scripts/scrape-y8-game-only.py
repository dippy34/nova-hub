#!/usr/bin/env python3
"""
Scrape only the game from y8.com (no wrapper)
"""
import requests
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def download_file(url, filepath, show_progress=False, current=0, total=0):
    """Download a file from URL with progress"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
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
                        print(f"\r    [{current}/{total}] Downloading {filepath.name}... {percent:.1f}% ({downloaded:,}/{total_size:,} bytes)", end='', flush=True)
        
        if show_progress:
            print(f"\r    [{current}/{total}] ✓ Downloaded {filepath.name} ({downloaded:,} bytes)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"\r    [{current}/{total}] ✗ Error downloading {filepath.name}: {e}", flush=True)
        else:
            print(f"      Error downloading {url}: {e}", flush=True)
        return False

def find_game_url(page_url):
    """Find the actual game embed URL from Y8 page"""
    print("  Searching for game embed URL...", flush=True)
    
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        content = r.text
    except Exception as e:
        print(f"    ✗ Error fetching page: {e}", flush=True)
        return None
    
    # Try to find game URL in various ways
    game_urls = []
    
    # Method 1: Look for y8games.com URLs
    y8games_matches = re.findall(r'https?://[^"\']*y8games\.com[^"\']*', content, re.I)
    game_urls.extend(y8games_matches)
    
    # Method 2: Look for game embed in script tags
    soup = BeautifulSoup(content, 'html.parser')
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for game URLs
            matches = re.findall(r'https?://[^"\']+\.(?:html|swf|unity|js|wasm)', script.string, re.I)
            game_urls.extend(matches)
            
            # Look for iframe src patterns
            iframe_src = re.search(r'iframe.*?src["\']:\s*["\']([^"\']+)["\']', script.string, re.I)
            if iframe_src:
                game_urls.append(iframe_src.group(1))
            
            # Look for gameId or game_id
            game_id_match = re.search(r'game[Ii]d["\']?\s*[:=]\s*["\']?(\d+)', script.string)
            if game_id_match:
                game_id = game_id_match.group(1)
                # Try common Y8 game URL patterns
                possible_urls = [
                    f"https://www.y8.com/games/{game_id}",
                    f"https://y8games.com/games/{game_id}",
                    f"https://www.y8.com/embed/{game_id}",
                ]
                game_urls.extend(possible_urls)
    
    # Method 3: Look for data attributes
    game_div = soup.find('div', {'data-game-id': True}) or soup.find('div', {'data-game': True})
    if game_div:
        game_id = game_div.get('data-game-id') or game_div.get('data-game')
        if game_id:
            game_urls.append(f"https://www.y8.com/embed/{game_id}")
    
    # Method 4: Look for canonical game URL from page
    canonical = soup.find('link', rel='canonical')
    if canonical and canonical.get('href'):
        canonical_url = canonical.get('href')
        # Try to get embed version
        if '/games/' in canonical_url:
            embed_url = canonical_url.replace('/games/', '/embed/')
            game_urls.append(embed_url)
    
    # Remove duplicates and filter
    game_urls = list(set(game_urls))
    game_urls = [url for url in game_urls if url and not any(x in url.lower() for x in ['account', 'profile', 'api', 'analytics'])]
    
    if game_urls:
        print(f"    ✓ Found {len(game_urls)} potential game URL(s)", flush=True)
        for url in game_urls[:3]:  # Show first 3
            print(f"      - {url[:80]}...", flush=True)
        # Prefer embed URLs
        embed_urls = [url for url in game_urls if '/embed/' in url or 'y8games.com' in url]
        if embed_urls:
            return embed_urls[0]
        return game_urls[0]
    else:
        # Try direct embed URL based on game slug
        path = urlparse(page_url).path
        if '/games/' in path:
            game_slug = path.split('/games/')[-1]
            embed_url = f"https://www.y8.com/embed/{game_slug}"
            print(f"    ⚠ Trying embed URL: {embed_url}", flush=True)
            return embed_url
    
    return None

def main():
    game_url = "https://www.y8.com/games/escape_tsunami_for_brainrots"
    
    print("Scraping game from y8.com (game only)...")
    print("=" * 60, flush=True)
    print(f"URL: {game_url}", flush=True)
    
    # Find the actual game URL
    print("\nFinding game embed URL...", flush=True)
    game_embed_url = find_game_url(game_url)
    
    if not game_embed_url:
        print("  ✗ Could not find game embed URL", flush=True)
        return
    
    print(f"  ✓ Game URL: {game_embed_url}", flush=True)
    
    # Fetch the game page
    print("\nFetching game page...", flush=True)
    try:
        r = requests.get(game_embed_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        game_html = r.text
        print(f"  ✓ Fetched {len(game_html)} bytes", flush=True)
    except Exception as e:
        print(f"  ✗ Error fetching game: {e}", flush=True)
        return
    
    # Parse game HTML
    game_soup = BeautifulSoup(game_html, 'html.parser')
    
    # Extract title
    title = "Escape Tsunami for Brainrots"
    title_tag = game_soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()
    
    # Get cover image
    cover_url = None
    og_image = game_soup.find('meta', property='og:image')
    if og_image:
        cover_url = og_image.get('content', '')
    
    # Create directory
    game_directory = slugify(title) or "escape-tsunami-for-brainrots"
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    print(f"\n  ✓ Directory: {game_directory}", flush=True)
    
    # Collect assets
    print("\nScanning for game assets...", flush=True)
    css_urls = []
    js_urls = []
    img_urls = []
    other_urls = []
    
    # Find CSS
    for link in game_soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            css_urls.append((urljoin(game_embed_url, href), link))
    
    # Find JavaScript
    for script in game_soup.find_all('script', src=True):
        src = script.get('src')
        if src and not src.startswith('data:'):
            js_urls.append((urljoin(game_embed_url, src), script))
    
    # Find images
    for img in game_soup.find_all('img', src=True):
        src = img.get('src')
        if src and not src.startswith('data:'):
            img_urls.append((urljoin(game_embed_url, src), img))
    
    # Find Unity/WebGL assets
    for script in game_soup.find_all('script'):
        if script.string:
            # Look for Unity build files
            unity_matches = re.findall(r'https?://[^"\']+\.(?:data|framework|loader|wasm|br)', script.string, re.I)
            for match in unity_matches:
                if match not in [url for url, _ in js_urls]:
                    js_urls.append((match, None))
            
            # Look for other asset URLs
            asset_matches = re.findall(r'https?://[^"\']+\.(?:png|jpg|jpeg|webp|svg|json|bin)', script.string, re.I)
            for match in asset_matches:
                if match not in [url for url, _ in css_urls + js_urls + img_urls]:
                    if match.endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                        img_urls.append((match, None))
                    else:
                        other_urls.append(match)
    
    total_files = len(css_urls) + len(js_urls) + len(img_urls) + len(other_urls)
    print(f"  Found {len(css_urls)} CSS, {len(js_urls)} JS, {len(img_urls)} images, {len(other_urls)} other ({total_files} total)", flush=True)
    
    # Download CSS
    css_files = []
    if css_urls:
        print(f"\n  Downloading CSS files ({len(css_urls)} files)...", flush=True)
        for idx, (css_url, link) in enumerate(css_urls, 1):
            css_filename = Path(urlparse(css_url).path).name or 'style.css'
            if '?' in css_filename:
                css_filename = css_filename.split('?')[0]
            css_path = game_path / css_filename
            if download_file(css_url, css_path, show_progress=True, current=idx, total=len(css_urls)):
                css_files.append(css_filename)
                if link:
                    link['href'] = css_filename
    
    # Download JavaScript
    js_files = []
    if js_urls:
        print(f"\n  Downloading JavaScript files ({len(js_urls)} files)...", flush=True)
        for idx, (js_url, script) in enumerate(js_urls, 1):
            js_filename = Path(urlparse(js_url).path).name or 'script.js'
            if '?' in js_filename:
                js_filename = js_filename.split('?')[0]
            js_path = game_path / js_filename
            if download_file(js_url, js_path, show_progress=True, current=idx, total=len(js_urls)):
                js_files.append(js_filename)
                if script:
                    script['src'] = js_filename
    
    # Download images
    img_files = []
    if img_urls:
        print(f"\n  Downloading images ({len(img_urls)} files)...", flush=True)
        for idx, (img_url, img) in enumerate(img_urls, 1):
            img_filename = Path(urlparse(img_url).path).name or 'image.png'
            if '?' in img_filename:
                img_filename = img_filename.split('?')[0]
            img_path = game_path / img_filename
            if download_file(img_url, img_path, show_progress=True, current=idx, total=len(img_urls)):
                img_files.append(img_filename)
                if img:
                    img['src'] = img_filename
    
    # Download other assets
    other_files = []
    if other_urls:
        print(f"\n  Downloading other assets ({len(other_urls)} files)...", flush=True)
        for idx, other_url in enumerate(other_urls, 1):
            other_filename = Path(urlparse(other_url).path).name or 'asset.bin'
            if '?' in other_filename:
                other_filename = other_filename.split('?')[0]
            other_path = game_path / other_filename
            if download_file(other_url, other_path, show_progress=True, current=idx, total=len(other_urls)):
                other_files.append(other_filename)
    
    # Update base tag
    base_tag = game_soup.find('base')
    if not base_tag:
        base_tag = game_soup.new_tag('base', href='./')
        if game_soup.head:
            game_soup.head.insert(0, base_tag)
    else:
        base_tag['href'] = './'
    
    # Save HTML
    print("\n  Saving HTML...", flush=True)
    html_file = game_path / "index.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(game_soup))
    print("    ✓ Saved index.html", flush=True)
    
    # Download cover
    if cover_url:
        print(f"\n  Downloading cover image...", flush=True)
        cover_file = game_path / "cover.png"
        if download_file(cover_url, cover_file):
            print("    ✓ Saved cover image", flush=True)
    
    # Update games.json
    print(f"\nUpdating games.json...", flush=True)
    games = []
    if GAMES_JSON_PATH.exists():
        with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
            games = json.load(f)
    
    existing = False
    for game in games:
        if game.get('directory') == game_directory:
            existing = True
            game['name'] = title
            game['image'] = 'cover.png' if cover_url else 'image.png'
            break
    
    if not existing:
        games.append({
            'name': title,
            'directory': game_directory,
            'image': 'cover.png' if cover_url else 'image.png',
            'source': 'non-semag'
        })
    
    with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent='\t', ensure_ascii=False)
    
    print("\n" + "=" * 60, flush=True)
    print("SCRAPE COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: {title}", flush=True)
    print(f"Directory: {game_directory}", flush=True)
    print(f"Files: {len(css_files)} CSS, {len(js_files)} JS, {len(img_files)} images, {len(other_files)} other", flush=True)
    print(f"Total: {len(css_files) + len(js_files) + len(img_files) + len(other_files)} files", flush=True)
    print(f"✓ Saved to games.json", flush=True)

if __name__ == "__main__":
    main()

