#!/usr/bin/env python3
"""
Download Unity build files for Escape Road games
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"

def download_file(url, filepath, silent=False):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        if not silent:
            print(f"    Error downloading {url}: {e}", flush=True)
        return False

def download_unity_build(game_dir, game_name, base_url):
    """Download Unity build files for a game"""
    html_file = game_dir / "index.html"
    if not html_file.exists():
        print(f"    ⚠ HTML file not found", flush=True)
        return False
    
    html_content = html_file.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract build URL and version folder from script tags
    build_url = None
    version_folder = None
    loader_url = None
    
    # Find the script that defines buildUrl and versionFolder
    # Try pattern 1: with versionFolder
    for script in soup.find_all('script'):
        script_text = script.string or ''
        if 'buildUrl' in script_text:
            # Pattern 1: with versionFolder
            if 'versionFolder' in script_text:
                # Extract versionFolder
                version_match = re.search(r"var versionFolder = ['\"]([^'\"]+)['\"]", script_text)
                if version_match:
                    version_folder = version_match.group(1)
                
                # Extract buildUrl
                build_match = re.search(r"var buildUrl = ['\"]([^'\"]+)['\"]", script_text)
                if build_match:
                    build_url = build_match.group(1)
                
                # Extract loaderUrl
                loader_match = re.search(r"var loaderUrl = buildUrl \+ ['\"]([^'\"]+)['\"]", script_text)
                if loader_match:
                    loader_url = loader_match.group(1)
                
                # Extract dataUrl, frameworkUrl, codeUrl
                data_match = re.search(r"dataUrl: buildUrl \+ ['\"]([^'\"]+)['\"]", script_text)
                framework_match = re.search(r"frameworkUrl: buildUrl \+ ['\"]([^'\"]+)['\"]", script_text)
                code_match = re.search(r"codeUrl: buildUrl \+ ['\"]([^'\"]+)['\"]", script_text)
                streaming_match = re.search(r"streamingAssetsUrl: versionFolder\+['\"]([^'\"]+)['\"]", script_text)
                
                if version_folder and build_url:
                    # Construct full paths
                    build_base = f"{version_folder}{build_url}"
                    
                    files_to_download = []
                    
                    if loader_url:
                        files_to_download.append(f"{build_base}{loader_url}")
                    
                    if data_match:
                        files_to_download.append(f"{build_base}{data_match.group(1)}")
                    
                    if framework_match:
                        files_to_download.append(f"{build_base}{framework_match.group(1)}")
                    
                    if code_match:
                        files_to_download.append(f"{build_base}{code_match.group(1)}")
                    
                    if streaming_match:
                        streaming_path = f"{version_folder}{streaming_match.group(1)}"
                        files_to_download.append(streaming_path)
                    
                    # Download all files
                    downloaded = 0
                    for file_path in files_to_download:
                        full_url = urljoin(base_url, file_path)
                        # Create local path preserving directory structure
                        local_path = game_dir / file_path.replace('/', '_').replace('\\', '_')
                        
                        # But try to preserve some structure for Build files
                        if 'Build' in file_path:
                            # Extract just the filename
                            filename = file_path.split('/')[-1]
                            build_dir = game_dir / version_folder.replace('/', '_') / "Build"
                            build_dir.mkdir(parents=True, exist_ok=True)
                            local_path = build_dir / filename
                        elif version_folder in file_path:
                            # Other version folder files
                            filename = file_path.replace(version_folder, '').lstrip('/')
                            version_dir = game_dir / version_folder.replace('/', '_')
                            version_dir.mkdir(parents=True, exist_ok=True)
                            local_path = version_dir / filename.replace('/', '_')
                        
                        print(f"    Downloading: {file_path.split('/')[-1]}...", flush=True)
                        if download_file(full_url, local_path, silent=True):
                            downloaded += 1
                            # Update HTML to use local path
                            relative_path = str(local_path.relative_to(game_dir)).replace('\\', '/')
                            html_content = html_content.replace(file_path, relative_path)
                    
                    # Update loaderUrl in script
                    if loader_url:
                        old_loader = f"var loaderUrl = buildUrl + \"{loader_url}\";"
                        new_loader_path = str((game_dir / version_folder.replace('/', '_') / "Build" / loader_url.split('/')[-1]).relative_to(game_dir)).replace('\\', '/')
                        new_loader = f"var loaderUrl = \"{new_loader_path}\";"
                        html_content = html_content.replace(old_loader, new_loader)
                    
                    # Update buildUrl to use local path
                    if build_url:
                        old_build = f"var buildUrl = \"{build_url}\";"
                        new_build_path = f"{version_folder.replace('/', '_')}/Build"
                        new_build = f"var buildUrl = \"{new_build_path}\";"
                        html_content = html_content.replace(old_build, new_build)
                    
                    # Save updated HTML
                    html_file.write_text(html_content, encoding='utf-8')
                    
                    print(f"    ✓ Downloaded {downloaded}/{len(files_to_download)} Unity build files", flush=True)
                    return downloaded > 0
            
            # Pattern 2: simple buildUrl without versionFolder (like escape-road-winter)
            elif 'const buildUrl' in script_text or 'var buildUrl' in script_text:
                build_match = re.search(r"(?:const|var)\s+buildUrl\s*=\s*['\"]([^'\"]+)['\"]", script_text)
                if build_match:
                    build_url = build_match.group(1)
                
                loader_match = re.search(r"const loaderUrl\s*=\s*buildUrl\s*\+\s*['\"]([^'\"]+)['\"]", script_text)
                if loader_match:
                    loader_url = loader_match.group(1)
                
                data_match = re.search(r"dataUrl:\s*buildUrl\s*\+\s*['\"]([^'\"]+)['\"]", script_text)
                framework_match = re.search(r"frameworkUrl:\s*buildUrl\s*\+\s*['\"]([^'\"]+)['\"]", script_text)
                code_match = re.search(r"codeUrl:\s*buildUrl\s*\+\s*['\"]([^'\"]+)['\"]", script_text)
                streaming_match = re.search(r"streamingAssetsUrl:\s*['\"]([^'\"]+)['\"]", script_text)
                
                if build_url:
                    files_to_download = []
                    
                    if loader_url:
                        files_to_download.append(f"{build_url}{loader_url}")
                    
                    if data_match:
                        files_to_download.append(f"{build_url}{data_match.group(1)}")
                    
                    if framework_match:
                        files_to_download.append(f"{build_url}{framework_match.group(1)}")
                    
                    if code_match:
                        files_to_download.append(f"{build_url}{code_match.group(1)}")
                    
                    if streaming_match:
                        files_to_download.append(streaming_match.group(1))
                    
                    # Download all files
                    downloaded = 0
                    for file_path in files_to_download:
                        full_url = urljoin(base_url, file_path)
                        # Create local path
                        if 'Build' in file_path:
                            filename = file_path.split('/')[-1]
                            build_dir = game_dir / "Build"
                            build_dir.mkdir(parents=True, exist_ok=True)
                            local_path = build_dir / filename
                        else:
                            filename = file_path.split('/')[-1]
                            local_path = game_dir / filename
                        
                        print(f"    Downloading: {filename}...", flush=True)
                        if download_file(full_url, local_path, silent=True):
                            downloaded += 1
                            # Update HTML to use local path
                            relative_path = str(local_path.relative_to(game_dir)).replace('\\', '/')
                            html_content = html_content.replace(file_path, relative_path)
                    
                    # Update loaderUrl
                    if loader_url:
                        old_loader = f"const loaderUrl = buildUrl + \"{loader_url}\";"
                        new_loader_path = f"Build/{loader_url.split('/')[-1]}"
                        new_loader = f"const loaderUrl = \"{new_loader_path}\";"
                        html_content = html_content.replace(old_loader, new_loader)
                    
                    # Save updated HTML
                    html_file.write_text(html_content, encoding='utf-8')
                    
                    print(f"    ✓ Downloaded {downloaded}/{len(files_to_download)} Unity build files", flush=True)
                    return downloaded > 0
    
    print(f"    ⚠ Could not find Unity build configuration", flush=True)
    return False

def main():
    print("Escape Road Unity Build Downloader")
    print("=" * 60, flush=True)
    
    # Map of game directories to their base URLs
    game_urls = {
        'escape-road': 'https://azgames.io/game/escape-road/',
        'escape-road-2': 'https://game.azgame.io/escape-road-2/',
        'escape-road-city': 'https://game.azgame.io/escape-road-city/',
        'escape-road-city-2': 'https://game.azgame.io/escape-road-city-2/',
        'escape-road-winter': 'https://azgames.io/game/escape-road-winter/',
        'escape-road-halloween': 'https://azgames.io/escape-road-halloween/',
    }
    
    downloaded_count = 0
    
    for i, (game_dir_name, base_url) in enumerate(game_urls.items(), 1):
        game_dir = GAMES_DIR / game_dir_name
        
        if not game_dir.exists():
            print(f"[{i}/{len(game_urls)}] ⚠ Directory not found: {game_dir_name}", flush=True)
            continue
        
        print(f"\n[{i}/{len(game_urls)}] Processing: {game_dir_name}", flush=True)
        
        if download_unity_build(game_dir, game_dir_name, base_url):
            downloaded_count += 1
            print(f"  ✓ Success: {game_dir_name}", flush=True)
        else:
            print(f"  ✗ Failed: {game_dir_name}", flush=True)
        
        time.sleep(1)  # Be polite
    
    print(f"\n" + "=" * 60, flush=True)
    print(f"DOWNLOAD SUMMARY", flush=True)
    print(f"=" * 60, flush=True)
    print(f"Successfully processed: {downloaded_count}/{len(game_urls)}", flush=True)

if __name__ == "__main__":
    main()

