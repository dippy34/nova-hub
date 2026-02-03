#!/usr/bin/env python3
"""Find index.json from codys-shack-games.pages.dev"""
import requests
import json

base_url = "https://codys-shack-games.pages.dev"

# Try common locations
urls_to_try = [
    f"{base_url}/index.json",
    f"{base_url}/projects/index.json",
    f"{base_url}/projects/hackertype/index.json",
    f"{base_url}/api/index.json",
    f"{base_url}/data/index.json",
    f"{base_url}/games/index.json",
]

print("Searching for index.json...")
print("=" * 60)

for url in urls_to_try:
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            print(f"\n[FOUND] {url}")
            print(f"Status: {r.status_code}")
            print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
            print(f"Content length: {len(r.text)} bytes")
            print("\nContent preview:")
            try:
                data = json.loads(r.text)
                print(json.dumps(data, indent=2)[:1000])
                if len(json.dumps(data, indent=2)) > 1000:
                    print("\n... (truncated)")
            except:
                print(r.text[:1000])
                if len(r.text) > 1000:
                    print("\n... (truncated)")
            print("\n" + "=" * 60)
            break
    except Exception as e:
        print(f"[FAIL] {url}: {e}")

# Also check the homepage for references
print("\nChecking homepage for index.json references...")
try:
    r = requests.get(base_url, timeout=10)
    import re
    matches = re.findall(r'["\']([^"\']*index\.json[^"\']*)["\']', r.text, re.I)
    if matches:
        print(f"Found {len(matches)} references in homepage:")
        for match in matches[:10]:
            full_url = f"{base_url}{match}" if match.startswith('/') else f"{base_url}/{match}"
            print(f"  - {full_url}")
            try:
                r2 = requests.get(full_url, timeout=10)
                if r2.status_code == 200:
                    print(f"    [FOUND] Status: {r2.status_code}, Length: {len(r2.text)}")
            except:
                pass
    else:
        print("  No index.json references found in homepage")
except Exception as e:
    print(f"Error checking homepage: {e}")


