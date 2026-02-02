#!/usr/bin/env python3
"""
Download a movie from arc018.to using Selenium to capture video URL
"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://arc018.to/',
}

def download_file(url, filepath, show_progress=True):
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
                        print(f"\r    Downloading: {percent:5.1f}% ({size_mb:.2f}/{total_mb:.2f} MB)", end='', flush=True)
        
        if show_progress:
            size_mb = downloaded / 1024 / 1024
            print(f"\r    [OK] Downloaded: {filepath.name} ({size_mb:.2f} MB)", flush=True)
        return True
    except Exception as e:
        if show_progress:
            print(f"\r    [FAIL] Error: {str(e)[:50]}", flush=True)
        return False

def find_video_url_static(soup, base_url):
    """Find video URL from static HTML (fallback)"""
    video_urls = []
    
    # Look for video tags
    for video in soup.find_all('video', src=True):
        src = video.get('src', '')
        if src:
            full_url = urljoin(base_url, src)
            video_urls.append(full_url)
    
    # Look for source tags inside video
    for video in soup.find_all('video'):
        for source in video.find_all('source', src=True):
            src = source.get('src', '')
            if src:
                full_url = urljoin(base_url, src)
                video_urls.append(full_url)
    
    return video_urls

def find_video_url_selenium(movie_url):
    """Find video URL using Selenium to capture network requests"""
    print("  Using Selenium to capture video URL...", flush=True)
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    video_urls = []
    
    try:
        print("  Navigating to page and waiting for video to load...", flush=True)
        driver.get(movie_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get iframe URLs first, then navigate to them
        iframe_urls = []
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"  Found {len(iframes)} iframe(s), collecting URLs...", flush=True)
            for iframe in iframes:
                try:
                    iframe_src = iframe.get_attribute('src')
                    if iframe_src and any(x in iframe_src.lower() for x in ['video', 'player', 'embed', 'stream']):
                        iframe_urls.append(iframe_src)
                        print(f"    Video iframe: {iframe_src[:80]}...", flush=True)
                except:
                    pass
        
        # Navigate to each iframe URL to find video
        for iframe_url in iframe_urls:
            try:
                print(f"    Checking: {iframe_url[:80]}...", flush=True)
                driver.get(iframe_url)
                time.sleep(5)
                
                # Check for video element
                videos = driver.find_elements(By.TAG_NAME, "video")
                for video in videos:
                    src = video.get_attribute('src')
                    if src:
                        video_urls.append(src)
                        print(f"      Found video src: {src[:100]}...", flush=True)
                    
                    # Check source elements
                    sources = video.find_elements(By.TAG_NAME, "source")
                    for source in sources:
                        src = source.get_attribute('src')
                        if src:
                            video_urls.append(src)
                            print(f"      Found video source: {src[:100]}...", flush=True)
            except Exception as e:
                print(f"      Error: {str(e)[:50]}", flush=True)
        
        # Wait for video element
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
        except:
            pass
        
        time.sleep(5)  # Give video time to load
        
        # Check for video element
        videos = driver.find_elements(By.TAG_NAME, "video")
        for video in videos:
            src = video.get_attribute('src')
            if src:
                video_urls.append(src)
            
            # Check source elements
            sources = video.find_elements(By.TAG_NAME, "source")
            for source in sources:
                src = source.get_attribute('src')
                if src:
                    video_urls.append(src)
        
        # Capture network requests - go back to main page first
        driver.get(movie_url)
        time.sleep(3)
        
        print("  Capturing network requests from main page...", flush=True)
        all_urls = []
        for entry in driver.get_log('performance'):
            try:
                log = json.loads(entry['message'])['message']
                if log['method'] in ['Network.responseReceived', 'Network.requestWillBeSent']:
                    if log['method'] == 'Network.responseReceived':
                        response = log['params']['response']
                        url = response['url']
                        mime_type = response.get('mimeType', '')
                    else:
                        request = log['params']['request']
                        url = request['url']
                        mime_type = ''
                    
                    all_urls.append((url, mime_type))
                    
                    # Look for video MIME types or video file extensions
                    is_video = False
                    if mime_type:
                        is_video = any(x in mime_type.lower() for x in ['video', 'mp4', 'webm', 'm3u8', 'x-matroska', 'application/vnd.apple.mpegurl'])
                    
                    if not is_video:
                        is_video = any(url.lower().endswith(ext) for ext in ['.mp4', '.webm', '.m3u8', '.mkv', '.avi', '.mov', '.flv', '.ts'])
                    
                    if is_video and url not in video_urls:
                        video_urls.append(url)
                        print(f"    Found video URL: {url[:120]}...", flush=True)
            except:
                pass
        
        # Also check the iframe page directly
        if iframe_urls:
            for iframe_url in iframe_urls[:1]:  # Check first video iframe
                try:
                    print(f"  Capturing from iframe: {iframe_url[:80]}...", flush=True)
                    driver.get(iframe_url)
                    time.sleep(10)  # Wait longer for video to load
                    
                    # Try to execute JavaScript to get video URL
                    try:
                        js_video_url = driver.execute_script("""
                            var video = document.querySelector('video');
                            if (video) {
                                if (video.src) return video.src;
                                var source = video.querySelector('source');
                                if (source && source.src) return source.src;
                            }
                            // Check for common video player variables
                            if (typeof player !== 'undefined' && player.getVideoUrl) {
                                return player.getVideoUrl();
                            }
                            if (typeof jwplayer !== 'undefined' && jwplayer().getPlaylist) {
                                var playlist = jwplayer().getPlaylist();
                                if (playlist && playlist[0] && playlist[0].file) return playlist[0].file;
                            }
                            return null;
                        """)
                        if js_video_url:
                            video_urls.append(js_video_url)
                            print(f"    Found video URL (JS): {js_video_url[:120]}...", flush=True)
                    except:
                        pass
                    
                    # Get fresh logs
                    for entry in driver.get_log('performance'):
                        try:
                            log = json.loads(entry['message'])['message']
                            if log['method'] in ['Network.responseReceived', 'Network.requestWillBeSent']:
                                if log['method'] == 'Network.responseReceived':
                                    response = log['params']['response']
                                    url = response['url']
                                    mime_type = response.get('mimeType', '')
                                else:
                                    request = log['params']['request']
                                    url = request['url']
                                    mime_type = ''
                                
                                is_video = False
                                if mime_type:
                                    is_video = any(x in mime_type.lower() for x in ['video', 'mp4', 'webm', 'm3u8', 'x-matroska', 'application/vnd.apple.mpegurl'])
                                
                                if not is_video:
                                    is_video = any(url.lower().endswith(ext) for ext in ['.mp4', '.webm', '.m3u8', '.mkv', '.avi', '.mov', '.ts'])
                                
                                # Also check for video-related domains (but exclude embed pages)
                                if not is_video:
                                    is_video = any(x in url.lower() for x in ['/video/', '/stream/', '/play/', '/movie/', 'videostr', 'streamtape'])
                                    # Exclude embed pages and HTML pages
                                    if is_video and any(x in url.lower() for x in ['/embed', '/iframe', '.html', 'favicon']):
                                        is_video = False
                                
                                if is_video and url not in video_urls and not any(x in url.lower() for x in ['ad', 'analytics', 'tracking', 'pixel', 'embed', 'iframe', 'favicon']):
                                    video_urls.append(url)
                                    print(f"    Found video URL (iframe): {url[:120]}...", flush=True)
                        except:
                            pass
                except Exception as e:
                    print(f"    Error: {str(e)[:50]}", flush=True)
        
        # Also check page source for video URLs (from iframe page)
        if iframe_urls:
            try:
                driver.get(iframe_urls[0])
                time.sleep(5)
                page_source = driver.page_source
                patterns = [
                    r'["\']([^"\']*\.mp4[^"\']*)["\']',
                    r'["\']([^"\']*\.m3u8[^"\']*)["\']',
                    r'["\']([^"\']*\.webm[^"\']*)["\']',
                    r'src["\']?\s*[:=]\s*["\']([^"\']*video[^"\']*\.mp4[^"\']*)["\']',
                    r'file["\']?\s*[:=]\s*["\']([^"\']*\.mp4[^"\']*)["\']',
                    r'url["\']?\s*[:=]\s*["\']([^"\']*\.mp4[^"\']*)["\']',
                    r'sources?["\']?\s*[:=]\s*\[([^\]]+)\]',
                    r'["\'](https?://[^"\']*videostr[^"\']*\.mp4[^"\']*)["\']',
                    r'["\'](https?://[^"\']*stream[^"\']*\.mp4[^"\']*)["\']',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, page_source, re.I)
                    for match in matches:
                        if isinstance(match, tuple):
                            url = match[0] if match[0] else ''
                        else:
                            url = match
                        # Clean up URL if it's in a sources array
                        if ',' in url:
                            for u in url.split(','):
                                u = u.strip().strip('"\'')
                                if u.startswith('http') and u not in video_urls:
                                    video_urls.append(u)
                                    print(f"    Found video URL (source): {u[:120]}...", flush=True)
                        elif url and url.startswith('http') and url not in video_urls:
                            video_urls.append(url)
                            print(f"    Found video URL (source): {url[:120]}...", flush=True)
            except:
                pass
        
    finally:
        driver.quit()
    
    return list(set(video_urls))  # Remove duplicates

def download_movie(movie_url):
    """Download movie from arc018.to"""
    print(f"Downloading movie from: {movie_url}")
    print("=" * 60, flush=True)
    
    try:
        # Fetch the page
        print("Step 1: Fetching movie page...", flush=True)
        response = requests.get(movie_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract movie title
        print("Step 2: Extracting movie information...", flush=True)
        title_tag = soup.find('title')
        movie_title = "Unknown Movie"
        if title_tag:
            movie_title = title_tag.text.replace(' - ARC018', '').replace(' | ARC018', '').strip()
        
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.text.strip():
            movie_title = h1_tag.text.strip()
        
        print(f"  Movie Title: {movie_title}", flush=True)
        
        # Find video URL using Selenium
        print("Step 3: Finding video URL...", flush=True)
        video_urls = find_video_url_selenium(movie_url)
        
        if not video_urls:
            # Fallback: try static parsing
            video_urls = find_video_url_static(soup, movie_url)
        
        if not video_urls:
            print("  [FAIL] Could not find video URL", flush=True)
            return False
        
        print(f"  Found {len(video_urls)} potential video URL(s):", flush=True)
        for i, url in enumerate(video_urls, 1):
            print(f"    {i}. {url[:80]}...", flush=True)
        
        # Try to download the first video URL
        video_url = video_urls[0]
        print(f"\nStep 4: Downloading video from: {video_url[:80]}...", flush=True)
        
        # Determine file extension
        parsed = urlparse(video_url)
        path = parsed.path
        if path.endswith('.mp4'):
            ext = '.mp4'
        elif path.endswith('.webm'):
            ext = '.webm'
        elif path.endswith('.m3u8'):
            ext = '.m3u8'
        else:
            ext = '.mp4'  # Default
        
        # Sanitize filename
        safe_title = re.sub(r'[^\w\-_\.]', '_', movie_title)
        output_dir = Path("downloads")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{safe_title}{ext}"
        
        if download_file(video_url, output_file):
            print(f"\n[SUCCESS] Movie downloaded to: {output_file}", flush=True)
            return True
        else:
            print(f"\n[FAIL] Failed to download video", flush=True)
            return False
        
    except Exception as e:
        import traceback
        print(f"\n[FAIL] Error: {e}", flush=True)
        traceback.print_exc()
        return False

if __name__ == "__main__":
    movie_url = "https://arc018.to/watch-movie/watch-five-nights-at-freddys-2-free-139258.12864523"
    download_movie(movie_url)

