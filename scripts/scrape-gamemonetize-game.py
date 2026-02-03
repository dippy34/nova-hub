import requests
from bs4 import BeautifulSoup
import json
import re
import sys
from urllib.parse import urlparse

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def scrape_gamemonetize_game(url):
    """Scrape a GameMonetize game and extract important fields only."""
    print(f"🎮 Scraping GameMonetize game from: {url}\n")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching URL: {e}")
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize game data
    game_data = {
        "id": "",
        "title": "",
        "url": url,
        "category": "",
        "tags": "",
        "thumb": ""
    }
    
    # Extract game ID from URL (usually in the path)
    # Example: https://html5.gamemonetize.com/rdo1rokdiqfmgwtg1on0mrrrxq3sal2y/
    url_path = urlparse(url).path.strip('/')
    if url_path:
        # Try to extract ID from path or use a hash of the path
        game_data["id"] = url_path.split('/')[-1] if url_path else ""
    
    # Try to find JSON-LD structured data
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if data.get('@type') == 'VideoGame' or 'game' in str(data).lower():
                    if 'name' in data:
                        game_data["title"] = data.get('name', '')
                    if 'image' in data:
                        game_data["thumb"] = data.get('image', '')
                    if 'genre' in data:
                        game_data["category"] = data.get('genre', '')
                    if 'keywords' in data:
                        game_data["tags"] = data.get('keywords', '')
        except:
            pass
    
    # Try to find meta tags
    # Title
    if not game_data["title"]:
        title_tag = soup.find('title')
        if title_tag:
            game_data["title"] = title_tag.get_text(strip=True)
        
        # Try og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            game_data["title"] = og_title['content']
    
    # Category
    if not game_data["category"]:
        # Try to find category in meta tags
        category_meta = soup.find('meta', {'name': re.compile('category|genre', re.I)})
        if category_meta and category_meta.get('content'):
            game_data["category"] = category_meta['content']
        
        # Try to find in script tags (GameMonetize often has game data in scripts)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for category/genre patterns
                category_match = re.search(r'["\']category["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string, re.I)
                if category_match:
                    game_data["category"] = category_match.group(1)
                    break
    
    # Tags
    if not game_data["tags"]:
        # Try to find in script tags first (more specific)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for tags field in game data object
                tags_match = re.search(r'["\']tags["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string, re.I)
                if tags_match:
                    tags_value = tags_match.group(1)
                    # Only use if it's not the generic "all games" list
                    if tags_value and len(tags_value) < 200:  # Reasonable tag length
                        game_data["tags"] = tags_value
                        break
        
        # Try meta keywords as fallback
        if not game_data["tags"]:
            keywords_meta = soup.find('meta', {'name': 'keywords'})
            if keywords_meta and keywords_meta.get('content'):
                keywords = keywords_meta['content']
                # Only use if it's not the generic "all games" list
                if keywords and len(keywords) < 200:
                    game_data["tags"] = keywords
    
    # Thumbnail
    if not game_data["thumb"]:
        # Try og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            game_data["thumb"] = og_image['content']
        
        # Try to find thumbnail in script tags (GameMonetize format)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for thumb/thumbnail patterns - GameMonetize specific
                thumb_match = re.search(r'["\']thumb["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string, re.I)
                if thumb_match:
                    game_data["thumb"] = thumb_match.group(1)
                    break
                
                # Look for img.gamemonetize.com URLs
                gamemonetize_img = re.search(r'https?://img\.gamemonetize\.com/[^"\'\s]+', script.string, re.I)
                if gamemonetize_img:
                    game_data["thumb"] = gamemonetize_img.group(0)
                    break
                
                # Also try image patterns
                img_match = re.search(r'["\']image["\']?\s*[:=]\s*["\']([^"\']+\.(jpg|jpeg|png|webp)[^"\']*)["\']', script.string, re.I)
                if img_match:
                    game_data["thumb"] = img_match.group(1)
                    break
        
        # Try to find img tags with common thumbnail classes/ids
        if not game_data["thumb"]:
            thumb_img = soup.find('img', {'id': re.compile('thumb|thumbnail|cover', re.I)})
            if not thumb_img:
                thumb_img = soup.find('img', {'class': re.compile('thumb|thumbnail|cover', re.I)})
            if thumb_img and thumb_img.get('src'):
                game_data["thumb"] = thumb_img['src']
        
        # Construct GameMonetize thumbnail URL if we have the ID but no thumb
        if not game_data["thumb"] and game_data["id"]:
            # GameMonetize thumbnail pattern: https://img.gamemonetize.com/{id}/512x384.jpg
            game_data["thumb"] = f"https://img.gamemonetize.com/{game_data['id']}/512x384.jpg"
    
    # Try to extract from GameMonetize API or embedded data
    # GameMonetize often has game data in window variables or script tags
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for GameMonetize game data structure
            # Pattern: {id: "...", title: "...", category: "...", tags: "...", thumb: "..."}
            game_obj_match = re.search(r'\{[^}]*["\']?(?:id|title|category|tags|thumb)["\']?\s*[:=]', script.string, re.I)
            if game_obj_match:
                # Try to extract a JSON-like object
                try:
                    # Find the object boundaries
                    start = script.string.find('{', game_obj_match.start())
                    if start != -1:
                        brace_count = 0
                        end = start
                        for i in range(start, min(start + 5000, len(script.string))):
                            if script.string[i] == '{':
                                brace_count += 1
                            elif script.string[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i + 1
                                    break
                        
                        if end > start:
                            obj_str = script.string[start:end]
                            # Try to parse as JSON (might need some cleaning)
                            obj_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', obj_str)  # Quote keys
                            try:
                                game_obj = json.loads(obj_str)
                                if 'title' in game_obj or 'id' in game_obj:
                                    game_data["id"] = game_obj.get('id', game_data["id"])
                                    game_data["title"] = game_obj.get('title', game_data["title"])
                                    game_data["category"] = game_obj.get('category', game_data["category"])
                                    game_data["tags"] = game_obj.get('tags', game_data["tags"])
                                    game_data["thumb"] = game_obj.get('thumb', game_data["thumb"])
                            except:
                                pass
                except:
                    pass
    
    # If ID is still empty, generate one from URL
    if not game_data["id"]:
        # Extract a unique identifier from the URL
        path_parts = urlparse(url).path.strip('/').split('/')
        if path_parts:
            game_data["id"] = path_parts[-1] or path_parts[0] if path_parts else ""
    
    # Default values if still empty
    if not game_data["tags"]:
        game_data["tags"] = "Games"
    if not game_data["category"]:
        game_data["category"] = "Action"  # Default category
    
    return game_data

def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape-gamemonetize-game.py <game_url>")
        print("Example: python scrape-gamemonetize-game.py https://html5.gamemonetize.com/rdo1rokdiqfmgwtg1on0mrrrxq3sal2y/")
        sys.exit(1)
    
    url = sys.argv[1]
    
    if 'gamemonetize.com' not in url:
        print("⚠️  Warning: URL doesn't appear to be a GameMonetize URL")
    
    game_data = scrape_gamemonetize_game(url)
    
    if game_data:
        # Output as JSON array (matching the format from the example)
        output = [game_data]
        print("\n✅ Scraped game data:")
        print(json.dumps(output, indent=2))
    else:
        print("\n❌ Failed to scrape game data")
        sys.exit(1)

if __name__ == "__main__":
    main()

