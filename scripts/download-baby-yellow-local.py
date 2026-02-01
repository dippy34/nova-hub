#!/usr/bin/env python3
"""
Download The Baby in Yellow game files locally and inject mock Yandex SDK
"""
import requests
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAME_DIR = GAMES_DIR / "the-baby-in-yellow-original-play-online-for-free-on-playhop"
BASE_URL = "https://app-483423.games.s3.yandex.net/483423/mg34gnj5p2awelrk661xc0z92z4eww8e_brotli/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

def download_file(url, filepath):
    """Download a file"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}", flush=True)
        return False

def main():
    print("Downloading The Baby in Yellow game files...")
    print("=" * 60, flush=True)
    
    # Download the main HTML file
    print("\nDownloading index.html...", flush=True)
    html_url = BASE_URL + "index.html"
    r = requests.get(html_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    html_content = r.text
    
    # Inject mock Yandex SDK at the beginning
    mock_sdk = """<script>
// Mock Yandex SDK
window.ysdk = window.ysdk || {
    getLanguage: function() { return navigator.language || 'en'; },
    getPayload: function() { return {}; },
    getPlayer: function() { 
        return {
            setData: function() { return Promise.resolve(); },
            getData: function() { return Promise.resolve({}); }
        };
    },
    getPayments: function() { 
        return {
            purchase: function() { return Promise.reject(); }
        };
    },
    getLeaderboards: function() { 
        return {
            setLeaderboardScore: function() { return Promise.resolve(); },
            getLeaderboardEntries: function() { return Promise.resolve({ entries: [] }); }
        };
    },
    getDeviceInfo: function() { 
        return { type: 'desktop', isMobile: false };
    },
    getEnvironment: function() { 
        return { app: { id: '483423' } };
    },
    init: function() { return Promise.resolve(this); },
    ready: function() { return Promise.resolve(); }
};
window.YaGames = window.YaGames || {
    init: function() { return Promise.resolve(window.ysdk); }
};
</script>
"""
    
    # Insert mock SDK right after <head> tag
    if '<head>' in html_content:
        html_content = html_content.replace('<head>', '<head>\n' + mock_sdk, 1)
    else:
        html_content = mock_sdk + html_content
    
    # Save modified HTML
    html_file = GAME_DIR / "index.html"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  ✓ Saved modified index.html with mock SDK", flush=True)
    
    # Extract and download referenced files
    print("\nExtracting file references...", flush=True)
    
    # Find script sources
    script_pattern = r'<script[^>]+src=["\']([^"\']+)["\']'
    scripts = re.findall(script_pattern, html_content)
    
    # Find link hrefs (CSS, etc.)
    link_pattern = r'<link[^>]+href=["\']([^"\']+)["\']'
    links = re.findall(link_pattern, html_content)
    
    all_files = set(scripts + links)
    
    print(f"Found {len(all_files)} referenced files", flush=True)
    
    # Download key files (limit to avoid too many downloads)
    key_files = [f for f in all_files if any(ext in f for ext in ['.js', '.css', '.json', '.wasm', '.data'])]
    
    print(f"\nDownloading {min(10, len(key_files))} key files...", flush=True)
    downloaded = 0
    for file_path in list(key_files)[:10]:
        if file_path.startswith('http'):
            file_url = file_path
        else:
            file_url = urljoin(BASE_URL, file_path.lstrip('/'))
        
        local_path = GAME_DIR / file_path.lstrip('/')
        if download_file(file_url, local_path):
            downloaded += 1
            print(f"  ✓ {file_path}", flush=True)
    
    print(f"\n✓ Downloaded {downloaded} files", flush=True)
    print(f"✓ Game files saved to {GAME_DIR}", flush=True)
    print("\nNote: The game may still need additional assets. If it doesn't work,", flush=True)
    print("you may need to download all Unity build files.", flush=True)

if __name__ == "__main__":
    main()

