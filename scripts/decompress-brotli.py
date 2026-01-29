#!/usr/bin/env python3
"""
Decompress brotli-compressed Unity WebGL files
"""
import os
import sys
from pathlib import Path

try:
    import brotli
except ImportError:
    print("Installing brotli library...")
    os.system(f"{sys.executable} -m pip install brotli")
    import brotli

def decompress_file(input_path, output_path):
    """Decompress a brotli-compressed file"""
    try:
        with open(input_path, 'rb') as f:
            compressed_data = f.read()
        
        decompressed_data = brotli.decompress(compressed_data)
        
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)
        
        print(f"✓ Decompressed: {input_path.name} -> {output_path.name} ({len(decompressed_data):,} bytes)")
        return True
    except Exception as e:
        print(f"✗ Failed to decompress {input_path.name}: {e}")
        return False

def main():
    game_dir = Path("non-semag/stickman-destruction-3-heroes")
    
    if not game_dir.exists():
        print(f"Error: {game_dir} does not exist")
        return
    
    print("🔧 Decompressing Unity WebGL files...")
    print("=" * 60)
    
    files_to_decompress = [
        ("bl3.framework.js.br", "bl3.framework.js"),
        ("bl3.wasm.br", "bl3.wasm"),
        ("bl3.data.br", "bl3.data")
    ]
    
    decompressed_count = 0
    for br_file, output_file in files_to_decompress:
        br_path = game_dir / br_file
        output_path = game_dir / output_file
        
        if br_path.exists():
            if decompress_file(br_path, output_path):
                decompressed_count += 1
        else:
            print(f"⚠️  File not found: {br_file}")
    
    print(f"\n✅ Decompressed {decompressed_count}/{len(files_to_decompress)} files")
    print(f"📁 Files are in: {game_dir.absolute()}")

if __name__ == "__main__":
    main()

