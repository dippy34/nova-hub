#!/usr/bin/env python3
"""Test nettleweb.com endpoints"""
import requests

endpoints = ['/games', '/api/games', '/api/v1/games', '/game/list', '/play']
base = 'https://nettleweb.com'

print("Testing nettleweb.com endpoints...")
for ep in endpoints:
    try:
        r = requests.get(f"{base}{ep}", timeout=5, allow_redirects=False)
        print(f"  {ep}: {r.status_code}")
        if r.status_code == 200 and len(r.text) > 100:
            print(f"    Content length: {len(r.text)}")
    except Exception as e:
        print(f"  {ep}: Error - {e}")

