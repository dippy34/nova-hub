#!/usr/bin/env python3
"""Get list of games from codys-shack-games GitHub repo"""
import requests
import json

api_url = "https://api.github.com/repos/theinfamouscoder5/codys-shack-games/contents/projects"
r = requests.get(api_url, timeout=10)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = json.loads(r.text)
    print(f"\nFound {len(data)} projects:\n")
    for item in data:
        if item.get('type') == 'dir':
            print(f"  - {item.get('name')}")
else:
    print(f"Error: {r.text}")


