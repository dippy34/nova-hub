#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

url = 'https://shsgames.github.io/g/4ead5539/kill-the-spartan'
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"Testing URL: {url}")
r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
print(f"Status: {r.status_code}")
print(f"Final URL: {r.url}")
print(f"Content length: {len(r.text)}")

if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')
    print("\nScripts found:")
    for script in soup.find_all('script', src=True):
        print(f"  - {script.get('src')}")
    
    print("\nChecking common Unity paths:")
    base = url.rstrip('/')
    paths = ['/index.html', '/Build/', '/build/', '/Build/loader.js', '/build/loader.js', '/loader.js']
    for p in paths:
        test_url = base + p
        try:
            test_r = requests.head(test_url, headers=headers, timeout=5, allow_redirects=True)
            print(f"  {test_url}: {test_r.status_code}")
        except:
            print(f"  {test_url}: Error")
    
    print("\nTrying raw GitHub paths:")
    github_base = 'https://raw.githubusercontent.com/shsgames/shsgames.github.io/main/g/4ead5539/kill-the-spartan'
    github_paths = ['/index.html', '/Build/loader.js', '/build/loader.js']
    for p in github_paths:
        test_url = github_base + p
        try:
            test_r = requests.head(test_url, headers=headers, timeout=5, allow_redirects=True)
            print(f"  {test_url}: {test_r.status_code}")
        except:
            print(f"  {test_url}: Error")

