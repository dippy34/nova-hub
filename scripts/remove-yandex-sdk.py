#!/usr/bin/env python3
"""
Remove Yandex SDK references from game HTML files
"""
import re
from pathlib import Path

def remove_yandex_sdk(html_path):
    """Remove Yandex SDK references from HTML file"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_len = len(content)
    
    # Remove Yandex SDK script tag
    content = re.sub(r'<!-- Yandex Games SDK -->\s*<script src="sdk\.js"></script>', '', content)
    
    # Remove InitYSDK function body and replace with simple stub
    content = re.sub(
        r'async function InitYSDK\(\) \{[^}]*try \{[^}]*if \(IsLocalHost\(\)\) return;[^}]*\} catch \(e\) \{[^}]*\}.*?if \(!IsLocalHost\(\) && !syncInit\)\s+StartUnityInstance_IfUnloaded\(\);',
        'async function InitYSDK() {\n            // Yandex SDK removed - start game immediately\n            if (IsLocalHost() || syncInit)\n                StartUnityInstance_IfUnloaded();\n        }',
        content,
        flags=re.DOTALL
    )
    
    # Replace InitYSDK call to just start the game
    content = re.sub(
        r'InstallBlurFocusBlocker\(\);\s*InitYSDK\(\);',
        'InstallBlurFocusBlocker();\n            StartUnityInstance_IfUnloaded();',
        content
    )
    
    # Make all Yandex SDK functions return early or do nothing
    yandex_functions = [
        'RequestingEnvironmentData', 'InitPlayer', 'LoadCloud', 'InitReview',
        'GetStats', 'InitPayments', 'GetAllGames', 'InitGameLabel', 'GetFlags'
    ]
    
    for func in yandex_functions:
        # Replace function bodies to return early
        pattern = rf'function {func}\([^)]*\) \{{[^}}]*return new Promise[^}}]*\}}'
        content = re.sub(
            pattern,
            f'function {func}() {{ return Promise.resolve("no data"); }}',
            content,
            flags=re.DOTALL
        )
    
    # Remove Yandex SDK variable assignments that might cause errors
    content = re.sub(r'ysdk = await[^;]*;', '// ysdk removed', content)
    content = re.sub(r'player = await[^;]*;', '// player removed', content)
    content = re.sub(r'payments = await[^;]*;', '// payments removed', content)
    
    # Make all Yandex SDK checks return early
    content = re.sub(r'if \(ysdk == null\)', 'if (true) // Yandex SDK removed', content)
    content = re.sub(r'if \(!ysdk\)', 'if (true) // Yandex SDK removed', content)
    content = re.sub(r'if \(ysdk !== null\)', 'if (false) // Yandex SDK removed', content)
    
    # Save the cleaned content
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    removed = original_len - len(content)
    print(f"Removed {removed:,} bytes of Yandex SDK code")
    return removed

if __name__ == "__main__":
    game_dir = Path(__file__).parent.parent / "non-semag" / "obby-tsunami-1-speed-play-online-for-free-on-playhop"
    html_file = game_dir / "index.html"
    
    if html_file.exists():
        print(f"Removing Yandex SDK from {html_file}...")
        remove_yandex_sdk(html_file)
        print("✓ Done")
    else:
        print(f"✗ File not found: {html_file}")

