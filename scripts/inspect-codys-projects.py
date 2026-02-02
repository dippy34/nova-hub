#!/usr/bin/env python3
"""Inspect codys-shack-games projects page to find game links"""
import requests
from bs4 import BeautifulSoup
import re

url = "https://codys-shack-games.pages.dev/projects"
r = requests.get(url, timeout=10)
print(f"Status: {r.status_code}")
print(f"Content length: {len(r.text)}")
print("\n" + "="*60)
print("HTML Content (first 3000 chars):")
print("="*60)
print(r.text[:3000])

soup = BeautifulSoup(r.text, 'html.parser')
print("\n" + "="*60)
print("All links found:")
print("="*60)
links = soup.find_all('a', href=True)
for link in links:
    href = link.get('href', '')
    text = link.get_text(strip=True)
    print(f"  {href} - '{text}'")

print("\n" + "="*60)
print("Script tags:")
print("="*60)
scripts = soup.find_all('script')
for i, script in enumerate(scripts):
    src = script.get('src', 'inline')
    print(f"  Script {i+1}: src={src}")
    if script.string and len(script.string) < 500:
        print(f"    Content: {script.string[:200]}")

print("\n" + "="*60)
print("Looking for /projects/ in all text:")
print("="*60)
matches = re.findall(r'/projects/[^"\'\s<>]+', r.text)
unique_matches = list(set(matches))
for match in unique_matches[:20]:
    print(f"  {match}")

