#!/usr/bin/env python3
"""
Convert Deadly Descent from iframe to local HTML (like Stickman Destruction)
"""
import json
from pathlib import Path
from urllib.parse import urlparse
import requests

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
GAMES_JSON_PATH = Path(__file__).parent.parent / "data" / "games.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.crazygames.com/',
}

def main():
    game_directory = "deadly-descent"
    game_embed_url = "https://deadly-descent-bzs.game-files.crazygames.com/deadly-descent-bzs/133/index.html"
    
    print("Converting Deadly Descent to local HTML (like Stickman Destruction)...")
    print("=" * 60, flush=True)
    
    game_path = GAMES_DIR / game_directory
    game_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Fetch the game HTML
        print("\nStep 1: Fetching game HTML...", flush=True)
        response = requests.get(game_embed_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        game_html = response.text
        print(f"  ✓ Fetched game HTML ({len(game_html)} bytes)", flush=True)
        
        # Extract base URL
        parsed_url = urlparse(game_embed_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
        
        # Create local HTML with base href and SDK mock
        print("\nStep 2: Creating local HTML wrapper...", flush=True)
        
        # Extract the body content from the game HTML
        # Find the body tag and extract its content
        body_start = game_html.find('<body')
        body_end = game_html.find('</body>')
        
        if body_start != -1 and body_end != -1:
            # Find the closing > of the body tag
            body_tag_end = game_html.find('>', body_start) + 1
            body_content = game_html[body_tag_end:body_end]
        else:
            # Fallback: use the entire HTML
            body_content = game_html
        
        # Extract head content (scripts, styles, etc.)
        head_start = game_html.find('<head')
        head_end = game_html.find('</head>')
        
        head_content = ""
        if head_start != -1 and head_end != -1:
            head_tag_end = game_html.find('>', head_start) + 1
            head_content = game_html[head_tag_end:head_end]
        
        # Create the local HTML
        local_html = f"""<!DOCTYPE html>
<html lang="en-us">
<head>
  <meta charset="utf-8">
  <base href="{base_url}">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>Deadly Descent</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
  <!-- Original head content -->
  {head_content}
  
  <!-- Mock CrazyGames SDK to prevent errors -->
  <script>
    (function() {{
      // Mock CrazySDK before the game loads
      window.CrazySDK = window.CrazySDK || {{}};
      
      const mockSDK = {{
        version: '3.3.1',
        environment: 'production',
        initOptions: {{}},
        init: function() {{
          return Promise.resolve({{
            version: '3.3.1',
            environment: 'production',
            initOptions: {{}}
          }});
        }},
        game: {{
          gameplayStart: function() {{}},
          gameplayStop: function() {{}},
          happyTime: function() {{}}
        }},
        ad: {{
          requestAd: function() {{
            return Promise.resolve({{}});
          }},
          hasAdblock: function() {{
            return false;
          }}
        }},
        user: {{
          getSDKVersion: function() {{
            return '3.3.1';
          }}
        }}
      }};
      
      if (window.CrazySDK) {{
        Object.assign(window.CrazySDK, mockSDK);
      }} else {{
        window.CrazySDK = mockSDK;
      }}
      
      if (typeof globalThis !== 'undefined') {{
        globalThis.CrazySDK = window.CrazySDK;
      }}
      
      const originalInit = window.CrazySDK.init;
      window.CrazySDK.init = function() {{
        try {{
          return originalInit ? originalInit.call(this) : Promise.resolve(mockSDK);
        }} catch (e) {{
          return Promise.resolve(mockSDK);
        }}
      }};
      
      console.log('CrazyGames SDK mocked');
    }})();
  </script>
</head>
<body>
{body_content}
</body>
</html>"""
        
        html_file = game_path / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(local_html)
        print(f"  ✓ Saved index.html", flush=True)
        
    except Exception as e:
        print(f"\n✗ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60, flush=True)
    print("CONVERSION COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Game: Deadly Descent", flush=True)
    print(f"Directory: {game_directory}", flush=True)
    print(f"Status: Now local HTML (not iframe) - like Stickman Destruction", flush=True)

if __name__ == "__main__":
    main()

