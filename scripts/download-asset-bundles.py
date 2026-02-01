#!/usr/bin/env python3
"""
Download asset bundles for Escape Tsunami game
"""
import requests
import json
from pathlib import Path
import re

GAME_DIR = Path(__file__).parent.parent / "non-semag" / "escape-tsunami-for-brainrots"
STREAMING_ASSETS_BASE = "https://storage.y8.com/y8-studio/unity_webgl/Playgama/escape_tsunami_for_brainrots/StreamingAssets"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

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
            print(f"\r    [{current}/{total}] ✗ {filepath.name[:45]:<45} Error", flush=True)
        return False

def main():
    print("Downloading asset bundles...")
    print("=" * 60, flush=True)
    
    # Read catalog
    catalog_file = GAME_DIR / "StreamingAssets" / "aa" / "catalog.json"
    if not catalog_file.exists():
        print("  ✗ Catalog file not found", flush=True)
        return
    
    with open(catalog_file, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    # Extract bundle names
    bundles = []
    for internal_id in catalog.get('m_InternalIds', []):
        if '.bundle' in internal_id:
            # Extract bundle filename
            bundle_match = re.search(r'([^/]+\.bundle)', internal_id)
            if bundle_match:
                bundle_name = bundle_match.group(1)
                bundles.append(bundle_name)
    
    # Remove duplicates
    bundles = list(set(bundles))
    
    print(f"  Found {len(bundles)} asset bundles", flush=True)
    
    # Download bundles
    print(f"\nDownloading asset bundles ({len(bundles)} files)...", flush=True)
    downloaded = []
    
    for idx, bundle_name in enumerate(bundles, 1):
        # Try WebGL path
        url = f"{STREAMING_ASSETS_BASE}/WebGL/{bundle_name}"
        local_path = GAME_DIR / "StreamingAssets" / "WebGL" / bundle_name
        
        if download_file(url, local_path, show_progress=True, current=idx, total=len(bundles)):
            downloaded.append(bundle_name)
    
    print("\n" + "=" * 60, flush=True)
    print("DOWNLOAD COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Bundles downloaded: {len(downloaded)}/{len(bundles)}", flush=True)

if __name__ == "__main__":
    main()

