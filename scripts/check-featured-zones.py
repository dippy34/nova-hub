#!/usr/bin/env python3
"""Check which featured zones are missing"""
import requests
import json
from pathlib import Path

ZONES_URL = "https://raw.githubusercontent.com/gn-math/assets/main/zones.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

# Load zones
print("Fetching zones.json...")
r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
r.raise_for_status()
zones_data = r.json()

# Get all featured zones
featured_zones = []
for zone in zones_data:
    if isinstance(zone, dict) and zone.get('featured') and zone.get('id') != -1:
        featured_zones.append(zone)

print(f"\nTotal featured zones: {len(featured_zones)}\n")
print("All featured zones:")
for z in featured_zones:
    print(f"  ID {z.get('id')}: {z.get('name')}")

# Load existing games
games_file = Path(__file__).parent.parent / "data" / "games.json"
with open(games_file, 'r', encoding='utf-8') as f:
    games = json.load(f)

existing_names = {g.get('name', '').lower() for g in games}
existing_dirs = {g.get('directory', '') for g in games}

print(f"\n\nChecking which featured zones are already in database...")
missing = []
already_have = []

for zone in featured_zones:
    name = zone.get('name', '')
    name_lower = name.lower()
    
    # Skip comments/suggestions
    if name.startswith('[!]'):
        print(f"  ⏭ Skipping (special): {name}")
        continue
    
    if name_lower in existing_names:
        already_have.append(name)
    else:
        missing.append((zone.get('id'), name))

print(f"\nAlready have: {len(already_have)}")
for name in already_have:
    print(f"  ✓ {name}")

print(f"\nMissing: {len(missing)}")
for zone_id, name in missing:
    print(f"  ✗ ID {zone_id}: {name}")


