#!/usr/bin/env python3
"""Find index.json or games list from codys-shack-games"""
import requests
import json
from bs4 import BeautifulSoup

base_url = "https://codys-shack-games.pages.dev"

print("Searching for index.json or games catalog...")
print("=" * 60)

# Try the projects page
print("\n1. Checking projects page...")
try:
    r = requests.get(f"{base_url}/projects/", timeout=10)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        # Look for links to JSON files
        links = soup.find_all('a', href=True)
        json_links = [l.get('href') for l in links if '.json' in l.get('href', '').lower()]
        if json_links:
            print(f"  Found {len(json_links)} JSON links:")
            for link in json_links[:10]:
                print(f"    - {link}")
        
        # Look for script tags that might reference index.json
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'index.json' in script.string:
                print("  Found reference to index.json in script!")
                # Extract the URL
                import re
                matches = re.findall(r'["\']([^"\']*index\.json[^"\']*)["\']', script.string)
                for match in matches:
                    full_url = f"{base_url}{match}" if match.startswith('/') else f"{base_url}/{match}"
                    print(f"    Trying: {full_url}")
                    try:
                        r2 = requests.get(full_url, timeout=10)
                        if r2.status_code == 200:
                            print(f"    [FOUND] {full_url}")
                            print(f"    Content: {r2.text[:500]}")
                    except:
                        pass
except Exception as e:
    print(f"  Error: {e}")

# Try common API/data endpoints
print("\n2. Trying common API endpoints...")
endpoints = [
    "/api/games.json",
    "/api/projects.json",
    "/data/games.json",
    "/data/projects.json",
    "/games.json",
    "/projects.json",
    "/_data/games.json",
    "/.well-known/games.json",
]

for endpoint in endpoints:
    try:
        url = f"{base_url}{endpoint}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print(f"  [FOUND] {url}")
            try:
                data = json.loads(r.text)
                print(f"    Valid JSON with {len(data) if isinstance(data, (list, dict)) else 'unknown'} items")
                print(f"    Preview: {json.dumps(data, indent=2)[:500]}")
            except:
                print(f"    Content: {r.text[:500]}")
    except:
        pass

# Check if there's a GitHub repo or source
print("\n3. Checking for source/GitHub links...")
try:
    r = requests.get(base_url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    github_links = [a.get('href') for a in soup.find_all('a', href=True) if 'github' in a.get('href', '').lower()]
    if github_links:
        print(f"  Found GitHub links: {github_links[:5]}")
except:
    pass

print("\n" + "=" * 60)

