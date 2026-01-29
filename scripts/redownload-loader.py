#!/usr/bin/env python3
"""Re-download the Unity loader.js file"""
import requests
from pathlib import Path

url = "https://files.crazygames.com/stickman-destruction-3-heroes/6/Build/bl3.loader.js"
output_path = Path("non-semag/stickman-destruction-3-heroes/bl3.loader.js")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.crazygames.com/',
    'Accept': '*/*'
}

print(f"Downloading {url}...")
response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, 'wb') as f:
    f.write(response.content)

print(f"✓ Downloaded {len(response.content)} bytes to {output_path}")
print(f"First 200 characters (as text):")
try:
    text = response.content[:200].decode('utf-8', errors='ignore')
    print(text)
except:
    print("(binary content)")

