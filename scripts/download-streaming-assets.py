#!/usr/bin/env python3
"""
Download StreamingAssets for Escape Tsunami game
"""
import requests
from pathlib import Path
import json

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAME_DIR = GAMES_DIR / "escape-tsunami-for-brainrots"
STREAMING_ASSETS_BASE = "https://storage.y8.com/y8-studio/unity_webgl/Playgama/escape_tsunami_for_brainrots/StreamingAssets"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

def download_file(url, filepath, show_progress=False, current=0, total=0):
    """Download a file with progress"""
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
                        size_kb = downloaded / 1024
                        total_kb = total_size / 1024 if total_size > 0 else 0
                        print(f"\r    [{current}/{total}] {filepath.name[:50]:<50} {percent:5.1f}% ({size_kb:.1f}/{total_kb:.1f} KB)", end='', flush=True)
        
        if show_progress:
            size_kb = downloaded / 1024
            print(f"\r    [{current}/{total}] ✓ {filepath.name[:50]:<50} ({size_kb:.1f} KB)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"\r    [{current}/{total}] ✗ {filepath.name[:50]:<50} Error", flush=True)
        return False

def main():
    print("Downloading StreamingAssets...")
    print("=" * 60, flush=True)
    
    # Known files to download
    files_to_download = [
        "aa/settings.json",
    ]
    
    # Try to get a directory listing or common files
    print("\nStep 1: Downloading known files...", flush=True)
    downloaded = []
    
    for file_path in files_to_download:
        url = f"{STREAMING_ASSETS_BASE}/{file_path}"
        local_path = GAME_DIR / "StreamingAssets" / file_path
        
        if download_file(url, local_path, show_progress=True, current=len(downloaded) + 1, total=len(files_to_download)):
            downloaded.append(file_path)
    
    # Try to discover more files by checking common patterns
    print("\nStep 2: Checking for additional files...", flush=True)
    
    # Common Unity StreamingAssets patterns
    common_paths = [
        "aa/manifest.json",
        "aa/manifest",
        "aa/aa",
        "aa/aa.json",
    ]
    
    additional = []
    for path in common_paths:
        url = f"{STREAMING_ASSETS_BASE}/{path}"
        try:
            r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                local_path = GAME_DIR / "StreamingAssets" / path
                if download_file(url, local_path, show_progress=True, current=len(downloaded) + len(additional) + 1, total=len(files_to_download) + len(common_paths)):
                    additional.append(path)
        except:
            pass
    
    print("\n" + "=" * 60, flush=True)
    print("DOWNLOAD COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Files downloaded: {len(downloaded) + len(additional)}", flush=True)
    print(f"  - Known files: {len(downloaded)}", flush=True)
    print(f"  - Additional files: {len(additional)}", flush=True)
    
    # Check if settings.json was downloaded and show content
    settings_file = GAME_DIR / "StreamingAssets" / "aa" / "settings.json"
    if settings_file.exists():
        print(f"\n✓ settings.json downloaded", flush=True)
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
                print(f"  Content preview: {str(content)[:100]}...", flush=True)
        except:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"  Content preview: {content[:100]}...", flush=True)

if __name__ == "__main__":
    main()


