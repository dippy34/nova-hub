import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*'
}

def download_gamemonetize_swf(game_url, output_dir=None):
    """Download the SWF file from a GameMonetize game page."""
    print(f"🎮 Downloading game from: {game_url}\n")
    
    # Get the HTML page
    try:
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching URL: {e}")
        return None
    
    # Find the SWF file
    swf_file = None
    
    # Look for player.load() calls
    match = re.search(r'player\.load\(["\']([^"\']+\.swf)["\']', html_content, re.I)
    if match:
        swf_file = match.group(1)
        print(f"✓ Found SWF file: {swf_file}")
    else:
        # Try other patterns
        swf_match = re.search(r'["\']([^"\']+\.swf)["\']', html_content, re.I)
        if swf_match:
            swf_file = swf_match.group(1)
            print(f"✓ Found SWF file (alternative): {swf_file}")
    
    if not swf_file:
        print("❌ Could not find SWF file in the page")
        return None
    
    # Construct full URL
    if swf_file.startswith('http'):
        swf_url = swf_file
    else:
        base_url = game_url.rstrip('/')
        if swf_file.startswith('/'):
            swf_url = f"https://html5.gamemonetize.com{swf_file}"
        else:
            swf_url = f"{base_url}/{swf_file}"
    
    print(f"📥 Downloading: {swf_url}")
    
    # Download the SWF file
    try:
        swf_response = requests.get(swf_url, headers=HEADERS, timeout=60, stream=True)
        swf_response.raise_for_status()
        
        # Determine output path
        if output_dir:
            output_path = Path(output_dir)
        else:
            # Extract game ID from URL
            from urllib.parse import urlparse
            path_parts = urlparse(game_url).path.strip('/').split('/')
            game_id = path_parts[-1] if path_parts else "game"
            output_path = Path(f"./scraped-gamemonetize-{game_id}")
        
        output_path.mkdir(exist_ok=True)
        
        swf_filename = Path(swf_file).name
        swf_path = output_path / swf_filename
        
        # Download the file
        total_size = int(swf_response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(swf_path, 'wb') as f:
            for chunk in swf_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print(f"\n✅ Downloaded: {swf_path.resolve()}")
        print(f"   Size: {swf_path.stat().st_size:,} bytes")
        
        # Also save the HTML for reference
        html_path = output_path / "index.html"
        html_path.write_text(html_content, encoding='utf-8')
        print(f"✅ Saved HTML: {html_path.resolve()}")
        
        return {
            'swf_path': str(swf_path),
            'swf_filename': swf_filename,
            'swf_url': swf_url,
            'html_path': str(html_path)
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading SWF: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python download-gamemonetize-swf.py <game_url> [output_dir]")
        print("Example: python download-gamemonetize-swf.py https://html5.gamemonetize.com/rdo1rokdiqfmgwtg1on0mrrrxq3sal2y/")
        sys.exit(1)
    
    game_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = download_gamemonetize_swf(game_url, output_dir)
    
    if result:
        print(f"\n📋 Summary:")
        print(f"   SWF file: {result['swf_filename']}")
        print(f"   SWF URL: {result['swf_url']}")
        print(f"   Local path: {result['swf_path']}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

