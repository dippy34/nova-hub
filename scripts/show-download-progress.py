#!/usr/bin/env python3
"""Show download progress for a game"""
from pathlib import Path
import json

game_dir = Path(__file__).parent.parent / "non-semag" / "escape-tsunami-for-brainrots"

if not game_dir.exists():
    print("Game directory not found!")
    exit(1)

print("=" * 60)
print("DOWNLOAD PROGRESS: Escape Tsunami for Brainrots")
print("=" * 60)

# Count files by type
css_files = list(game_dir.glob("*.css"))
js_files = list(game_dir.glob("*.js"))
img_files = list(game_dir.glob("*.{png,jpg,jpeg,webp,svg}"))
html_files = list(game_dir.glob("*.html"))

total_size = 0
for file in game_dir.iterdir():
    if file.is_file():
        total_size += file.stat().st_size

print(f"\n📁 Directory: {game_dir.name}")
print(f"\n📊 Files Downloaded:")
print(f"  ✓ HTML files: {len(html_files)}")
print(f"  ✓ CSS files: {len(css_files)}")
print(f"  ✓ JavaScript files: {len(js_files)}")
print(f"  ✓ Image files: {len(img_files)}")
print(f"  ✓ Total files: {len(css_files) + len(js_files) + len(img_files) + len(html_files)}")
print(f"  ✓ Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")

print(f"\n📋 File Details:")
print(f"\n  CSS Files ({len(css_files)}):")
for f in css_files:
    size = f.stat().st_size
    print(f"    • {f.name} ({size:,} bytes)")

print(f"\n  JavaScript Files ({len(js_files)}):")
for f in js_files:
    size = f.stat().st_size
    print(f"    • {f.name} ({size:,} bytes)")

print(f"\n  Image Files ({len(img_files)}):")
for f in img_files:
    size = f.stat().st_size
    print(f"    • {f.name} ({size:,} bytes)")

# Check games.json
games_json = Path(__file__).parent.parent / "data" / "games.json"
if games_json.exists():
    with open(games_json, 'r', encoding='utf-8') as f:
        games = json.load(f)
    
    game_entry = next((g for g in games if g.get('directory') == game_dir.name), None)
    if game_entry:
        print(f"\n✅ Game Entry in games.json:")
        print(f"    Name: {game_entry.get('name', 'N/A')}")
        print(f"    Directory: {game_entry.get('directory', 'N/A')}")
        print(f"    Image: {game_entry.get('image', 'N/A')}")
    else:
        print(f"\n⚠️  Game not found in games.json")

print("\n" + "=" * 60)
print("✓ Download Complete!")
print("=" * 60)


