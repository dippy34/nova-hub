#!/usr/bin/env python3
"""
Scrape 20 games from CrazyGames.com (like Deadly Descent) - with duplicate checking
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
    'Referer': 'https://www.crazygames.com/',
}

def sanitize_filename(name):
    """Sanitize filename"""
    return re.sub(r'[^\w\-_\.]', '_', name).lower()

def download_file(url, filepath):
    """Download a file"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
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
                # Also add sanitized version
                existing_names.add(sanitize_filename(name))
    
    return existing_dirs, existing_urls, existing_names

def find_game_urls_from_homepage():
    """Find game URLs from CrazyGames homepage"""
    print("Fetching CrazyGames homepage...", flush=True)
    try:
        response = requests.get("https://www.crazygames.com/", headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        game_urls = []
        seen = set()
        
        # Method 1: Find links with /game/ in href
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/game/' in href and href not in seen:
                full_url = urljoin("https://www.crazygames.com", href)
                # Clean URL (remove query params and fragments)
                clean_url = full_url.split('?')[0].split('#')[0].rstrip('/')
                if clean_url not in seen:
                    seen.add(clean_url)
                    game_urls.append(clean_url)
        
        # Method 2: Look in script tags for game data
        for script in soup.find_all('script'):
            if script.string:
                # Look for JSON data with game URLs
                matches = re.findall(r'["\'](/game/[^"\']+)["\']', script.string)
                for match in matches:
                    full_url = urljoin("https://www.crazygames.com", match)
                    clean_url = full_url.split('?')[0].split('#')[0].rstrip('/')
                    if clean_url not in seen:
                        seen.add(clean_url)
                        game_urls.append(clean_url)
        
        # Method 3: Try popular games page
        try:
            popular_response = requests.get("https://www.crazygames.com/popular-games", headers=HEADERS, timeout=30)
            if popular_response.status_code == 200:
                popular_soup = BeautifulSoup(popular_response.text, 'html.parser')
                for link in popular_soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if '/game/' in href:
                        full_url = urljoin("https://www.crazygames.com", href)
                        clean_url = full_url.split('?')[0].split('#')[0].rstrip('/')
                        if clean_url not in seen:
                            seen.add(clean_url)
                            game_urls.append(clean_url)
        except:
            pass
        
        return list(seen)[:100]  # Return up to 100 URLs to try
        
    except Exception as e:
        print(f"  ✗ Error fetching homepage: {e}", flush=True)
        return []

def find_game_embed_url(game_url, soup):
    """Find the actual game embed URL from the game page"""
    # Method 1: Look in script tags for game-files URLs
    for script in soup.find_all('script'):
        if script.string:
            # More comprehensive patterns
            patterns = [
                r'https://[^"\']*\.game-files\.crazygames\.com[^"\']*index\.html[^"\']*',
                r'https://[^"\']*game-files[^"\']*\.crazygames[^"\']*index\.html[^"\']*',
                r'["\'](https://[^"\']*game-files[^"\']*index\.html[^"\']*)["\']',
                r'gameUrl["\']?\s*[:=]\s*["\']([^"\']*game-files[^"\']*index\.html[^"\']*)["\']',
                r'src["\']?\s*[:=]\s*["\']([^"\']*game-files[^"\']*index\.html[^"\']*)["\']',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script.string, re.I)
                for match in matches:
                    if isinstance(match, tuple):
                        url = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                    else:
                        url = match
                    if url and 'game-files' in url and 'index.html' in url:
                        return url
    
    # Method 2: Look for iframe src or data attributes
    for iframe in soup.find_all('iframe', src=True):
        src = iframe.get('src', '')
        if 'game-files' in src and 'index.html' in src:
            return src
    
    # Method 3: Try to construct from game slug
    game_slug = game_url.split('/game/')[-1].rstrip('/')
    if game_slug:
        # Try multiple version patterns
        potential_urls = [
            f"https://{game_slug}.game-files.crazygames.com/{game_slug}/133/index.html",
            f"https://{game_slug}.game-files.crazygames.com/{game_slug}/index.html",
            f"https://{game_slug}-bzs.game-files.crazygames.com/{game_slug}-bzs/133/index.html",
            f"https://{game_slug}-bzs.game-files.crazygames.com/{game_slug}-bzs/index.html",
        ]
        for url in potential_urls:
            try:
                test_response = requests.head(url, headers={**HEADERS, 'Referer': game_url}, timeout=10)
                if test_response.status_code == 200:
                    return url
            except:
                pass
    
    return None

def scrape_crazygames_game(game_url, existing_dirs, existing_urls, existing_names):
    """Scrape a single game from CrazyGames"""
    try:
        # Fetch the game page
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract game name
        title_tag = soup.find('title')
        game_name = "Unknown Game"
        if title_tag:
            game_name = title_tag.text.replace(' - CrazyGames', '').replace(' | CrazyGames', '').replace('Play ', '').strip()
        
        # Also try h1 or meta tags
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.text.strip():
            game_name = h1_tag.text.strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            game_name = og_title.get('content').replace(' - CrazyGames', '').strip()
        
        # Clean up game name - remove emojis and extra text
        # Remove all emojis (Unicode emoji ranges) and variation selectors
        game_name = re.sub(r'[\U0001F000-\U0001F9FF\U0001FA00-\U0001FAFF]', '', game_name)
        game_name = re.sub(r'[\ufe00-\ufe0f]', '', game_name)  # Remove variation selectors
        # Remove "Play on CrazyGames" and similar suffixes
        game_name = re.sub(r'\s*play\s+on\s+crazygames.*$', '', game_name, flags=re.I)
        game_name = game_name.strip()
        
        if not game_name or game_name == "Unknown Game":
            return None, "Could not extract game name"
        
        # Check for duplicates by name FIRST (before creating directory)
        # Normalize name for comparison (remove special chars, lowercase, remove common suffixes)
        game_name_normalized = re.sub(r'[^\w\s]', '', game_name.lower()).strip()
        # Remove common suffixes like "io", "online", etc for comparison
        game_name_normalized = re.sub(r'\s+(io|online|game|play)$', '', game_name_normalized)
        game_name_sanitized = sanitize_filename(game_name)
        
        # Check exact matches
        if game_name.lower() in existing_names or game_name_sanitized in existing_names:
            return None, f"Already exists (name: {game_name})"
        
        # Check fuzzy matches - if normalized name matches any existing normalized name
        for existing_name in existing_names:
            existing_normalized = re.sub(r'[^\w\s]', '', existing_name.lower()).strip()
            existing_normalized = re.sub(r'\s+(io|online|game|play)$', '', existing_normalized)
            
            # Also remove ".io" from the end if present (for cases like "cubes 2048.io" vs "cubes 2048")
            game_name_for_compare = re.sub(r'\.io$', '', game_name_normalized)
            existing_for_compare = re.sub(r'\.io$', '', existing_normalized)
            
            # Check exact match after removing .io
            if game_name_for_compare == existing_for_compare and len(game_name_for_compare) > 3:
                return None, f"Already exists (similar: {game_name} vs {existing_name})"
            
            # Compare core words (split and check if most words match)
            game_words = set(game_name_for_compare.split())
            existing_words = set(existing_for_compare.split())
            
            # Remove common words like "the", "a", "an", "of", "in", "on", "at", "to", "for"
            common_stopwords = {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but'}
            game_words = game_words - common_stopwords
            existing_words = existing_words - common_stopwords
            
            # If they share significant words (at least 2 words or one is subset of other)
            if len(game_words) > 0 and len(existing_words) > 0:
                common_words = game_words & existing_words
                # If they share most words or one contains the other
                if len(common_words) >= min(2, len(game_words), len(existing_words)):
                    if len(game_name_for_compare) > 3 and len(existing_for_compare) > 3:
                        return None, f"Already exists (similar: {game_name} vs {existing_name})"
                # Also check if one is contained in the other (but be more strict)
                elif (game_name_for_compare in existing_for_compare or existing_for_compare in game_name_for_compare):
                    # Only match if the shorter one is at least 5 chars and the longer one contains it
                    shorter = min(game_name_for_compare, existing_for_compare, key=len)
                    longer = max(game_name_for_compare, existing_for_compare, key=len)
                    if len(shorter) >= 5 and shorter in longer:
                        return None, f"Already exists (similar: {game_name} vs {existing_name})"
        
        # Sanitize directory name
        game_directory = sanitize_filename(game_name)
        
        # Check for duplicates by directory
        if game_directory.lower() in existing_dirs:
            return None, f"Already exists (directory: {game_directory})"
        
        # Find the game embed URL
        game_embed_url = find_game_embed_url(game_url, soup)
        
        if not game_embed_url:
            return None, "Could not find game embed URL"
        
        # Check if URL already exists
        game_url_path = f"non-semag/{game_directory}/index.html"
        if game_url_path.lower() in existing_urls:
            return None, "Already exists (URL)"
        
        # Create directory
        game_path = GAMES_DIR / game_directory
        game_path.mkdir(parents=True, exist_ok=True)
        
        # Fetch the game HTML
        game_response = requests.get(game_embed_url, headers={**HEADERS, 'Referer': game_url}, timeout=30)
        if game_response.status_code != 200:
            return None, f"Game page returned {game_response.status_code}"
        
        game_html = game_response.text
        
        # Extract base URL
        parsed_url = urlparse(game_embed_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
        
        # Extract body and head content
        body_start = game_html.find('<body')
        body_end = game_html.find('</body>')
        
        body_content = ""
        if body_start != -1 and body_end != -1:
            body_tag_end = game_html.find('>', body_start) + 1
            body_content = game_html[body_tag_end:body_end]
        else:
            body_content = game_html
        
        head_start = game_html.find('<head')
        head_end = game_html.find('</head>')
        
        head_content = ""
        if head_start != -1 and head_end != -1:
            head_tag_end = game_html.find('>', head_start) + 1
            head_content = game_html[head_tag_end:head_end]
        
        # Download cover image
        cover_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_url = og_image.get('content', '')
        
        cover_file = game_path / "cover.png"
        if cover_url:
            cover_url = urljoin(game_url, cover_url)
            download_file(cover_url, cover_file)
        
        # Create local HTML
        local_html = f"""<!DOCTYPE html>
<html lang="en-us">
<head>
  <meta charset="utf-8">
  <base href="{base_url}">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>{game_name}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
  <!-- Original head content -->
  {head_content}
  
  <!-- Mock CrazyGames SDK to prevent errors -->
  <script>
    (function() {{
      window.CrazySDK = window.CrazySDK || {{}};
      
      const mockSDK = {{
        version: '3.3.1',
        environment: 'production',
        initOptions: {{}},
        init: function() {{
          return Promise.resolve({{
            version: '3.3.1',
            environment: 'production',
            initOptions: {{}}
          }});
        }},
        game: {{
          gameplayStart: function() {{}},
          gameplayStop: function() {{}},
          happyTime: function() {{}}
        }},
        ad: {{
          requestAd: function() {{
            return Promise.resolve({{}});
          }},
          hasAdblock: function() {{
            return false;
          }}
        }},
        user: {{
          getSDKVersion: function() {{
            return '3.3.1';
          }}
        }}
      }};
      
      if (window.CrazySDK) {{
        Object.assign(window.CrazySDK, mockSDK);
      }} else {{
        window.CrazySDK = mockSDK;
      }}
      
      if (typeof globalThis !== 'undefined') {{
        globalThis.CrazySDK = window.CrazySDK;
      }}
      
      const originalInit = window.CrazySDK.init;
      window.CrazySDK.init = function() {{
        try {{
          return originalInit ? originalInit.call(this) : Promise.resolve(mockSDK);
        }} catch (e) {{
          return Promise.resolve(mockSDK);
        }}
      }};
      
      console.log('CrazyGames SDK mocked');
    }})();
  </script>
</head>
<body>
{body_content}
</body>
</html>"""
        
        html_file = game_path / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(local_html)
        
        return {
            'name': game_name,
            'directory': game_directory,
            'image': 'cover.png',
            'source': 'non-semag',
            'url': game_url_path,
            'is_local': True
        }, "Success"
        
    except Exception as e:
        import traceback
        return None, f"Error: {str(e)[:100]}"

def main():
    print("Scraping 20 games from CrazyGames.com...")
    print("=" * 60, flush=True)
    
    # Get existing games
    existing_dirs, existing_urls, existing_names = get_existing_games()
    print(f"Found {len(existing_dirs)} existing games", flush=True)
    
    # Find game URLs from multiple pages
    print("\nStep 1: Finding game URLs from CrazyGames...", flush=True)
    all_game_urls = []
    seen_urls = set()
    
    # Try homepage
    homepage_urls = find_game_urls_from_homepage()
    for url in homepage_urls:
        if url not in seen_urls:
            seen_urls.add(url)
            all_game_urls.append(url)
    
    # Try popular games page
    try:
        print("  Trying popular games page...", flush=True)
        popular_response = requests.get("https://www.crazygames.com/popular-games", headers=HEADERS, timeout=30)
        if popular_response.status_code == 200:
            popular_soup = BeautifulSoup(popular_response.text, 'html.parser')
            for link in popular_soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/game/' in href:
                    full_url = urljoin("https://www.crazygames.com", href)
                    clean_url = full_url.split('?')[0].split('#')[0].rstrip('/')
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        all_game_urls.append(clean_url)
    except:
        pass
    
    # Try new games page
    try:
        print("  Trying new games page...", flush=True)
        new_response = requests.get("https://www.crazygames.com/new-games", headers=HEADERS, timeout=30)
        if new_response.status_code == 200:
            new_soup = BeautifulSoup(new_response.text, 'html.parser')
            for link in new_soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/game/' in href:
                    full_url = urljoin("https://www.crazygames.com", href)
                    clean_url = full_url.split('?')[0].split('#')[0].rstrip('/')
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        all_game_urls.append(clean_url)
    except:
        pass
    
    game_urls = all_game_urls[:100]  # Limit to 100 URLs to try
    
    if not game_urls:
        print("  Could not find any game URLs", flush=True)
        return
    
    print(f"  Found {len(game_urls)} potential game URLs", flush=True)
    
    # Scrape games
    print(f"\nStep 2: Scraping games (target: 20, showing progress)...", flush=True)
    scraped_games = []
    skipped = 0
    failed = 0
    
    for idx, game_url in enumerate(game_urls, 1):
        if len(scraped_games) >= 20:
            print(f"\n  ✓ Reached 20 games! Stopping...", flush=True)
            break
        
        print(f"\n[{idx}/{len(game_urls)}] Processing: {game_url[:60]}...", flush=True)
        
        game_entry, status = scrape_crazygames_game(game_url, existing_dirs, existing_urls, existing_names)
        
        if game_entry:
            scraped_games.append(game_entry)
            existing_dirs.add(game_entry['directory'].lower())
            existing_urls.add(game_entry['url'].lower())
            existing_names.add(game_entry['name'].lower())
            existing_names.add(sanitize_filename(game_entry['name']))
            print(f"  [OK] {game_entry['name']} - {status}", flush=True)
            print(f"    Progress: {len(scraped_games)}/20 games scraped", flush=True)
        elif "Already exists" in status:
            skipped += 1
            # Remove emojis from status message for safe printing
            safe_status = re.sub(r'[\U0001F000-\U0001F9FF\U0001FA00-\U0001FAFF]', '', status)
            safe_status = re.sub(r'[\ufe00-\ufe0f]', '', safe_status)
            print(f"  [SKIP] Skipped: {safe_status}", flush=True)
        else:
            failed += 1
            print(f"  [FAIL] Failed: {status}", flush=True)
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
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
        
        # Remove existing entries if they exist (double-check)
        for new_game in scraped_games:
            games_list = [g for g in games_list if g.get("directory") != new_game['directory']]
        
        # Add new games
        games_list.extend(scraped_games)
        
        if isinstance(games_data, dict):
            games_data["games"] = games_list
        else:
            games_data = games_list
        
        with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(games_data, f, indent='\t', ensure_ascii=False)
        
        print(f"  Added {len(scraped_games)} games to games.json", flush=True)
    
    # Summary
    print("\n" + "=" * 60, flush=True)
    print("SCRAPING COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Successfully scraped: {len(scraped_games)} games", flush=True)
    print(f"Skipped (already exist): {skipped} games", flush=True)
    print(f"Failed: {failed} games", flush=True)
    print(f"Total processed: {idx} URLs", flush=True)
    
    if scraped_games:
        print(f"\nScraped games:", flush=True)
        for game in scraped_games:
            print(f"  - {game['name']}", flush=True)

if __name__ == "__main__":
    main()
