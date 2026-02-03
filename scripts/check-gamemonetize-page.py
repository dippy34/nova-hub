import requests
from bs4 import BeautifulSoup

url = 'https://html5.gamemonetize.com/rdo1rokdiqfmgwtg1on0mrrrxq3sal2y/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

print("=== Page Analysis ===\n")
print(f"Title: {soup.title.string if soup.title else 'No title'}\n")

print("=== Iframes ===")
iframes = soup.find_all('iframe')
print(f"Found {len(iframes)} iframe tags")
for iframe in iframes:
    print(f"  - src: {iframe.get('src', 'no src')}")
    print(f"    id: {iframe.get('id', 'no id')}")
    print(f"    class: {iframe.get('class', 'no class')}")

print("\n=== Scripts ===")
scripts = soup.find_all('script')
print(f"Found {len(scripts)} script tags")
for i, script in enumerate(scripts[:5]):  # First 5
    src = script.get('src', 'inline')
    print(f"  Script {i+1}: {src}")
    if src == 'inline' and script.string:
        preview = script.string[:200].replace('\n', ' ')
        print(f"    Preview: {preview}...")

print("\n=== Canvas/Game Elements ===")
canvas = soup.find_all('canvas')
print(f"Found {len(canvas)} canvas tags")

game_divs = soup.find_all(['div', 'div'], {'id': lambda x: x and 'game' in x.lower()})
print(f"Found {len(game_divs)} divs with 'game' in id")

print("\n=== First 1000 chars of HTML ===")
print(soup.prettify()[:1000])

