import requests
import re

url = 'https://html5.gamemonetize.com/rdo1rokdiqfmgwtg1on0mrrrxq3sal2y/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get(url, headers=headers)
html = r.text

print("=== Looking for game file ===\n")

# Look for player.load() calls
match = re.search(r'player\.load\(["\']([^"\']+)["\']', html)
if match:
    game_file = match.group(1)
    print(f"Found game file: {game_file}")
    
    # Check if it's a relative or absolute URL
    if game_file.startswith('http'):
        print(f"  Full URL: {game_file}")
    else:
        # Construct full URL
        base_url = url.rstrip('/')
        if game_file.startswith('/'):
            full_url = f"https://html5.gamemonetize.com{game_file}"
        else:
            full_url = f"{base_url}/{game_file}"
        print(f"  Full URL: {full_url}")
else:
    print("No player.load() found")

# Look for other game file patterns
print("\n=== Other potential game files ===")
swf_files = re.findall(r'["\']([^"\']+\.swf[^"\']*)["\']', html, re.I)
if swf_files:
    for swf in set(swf_files):
        print(f"  SWF: {swf}")

# Look for object/embed tags
print("\n=== Object/Embed tags ===")
object_tags = re.findall(r'<object[^>]+data=["\']([^"\']+)["\']', html, re.I)
embed_tags = re.findall(r'<embed[^>]+src=["\']([^"\']+)["\']', html, re.I)
for obj in object_tags:
    print(f"  Object data: {obj}")
for emb in embed_tags:
    print(f"  Embed src: {emb}")

# Show the script section
print("\n=== Script section with game loading ===")
script_match = re.search(r'<script[^>]*>(.*?player\.load.*?)</script>', html, re.DOTALL | re.I)
if script_match:
    script_content = script_match.group(1)
    print(script_content[:800])

