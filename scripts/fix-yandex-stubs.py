#!/usr/bin/env python3
"""Remove leftover code after Yandex SDK stub functions"""
import re
from pathlib import Path

html_path = Path(__file__).parent.parent / "non-semag" / "obby-tsunami-1-speed-play-online-for-free-on-playhop" / "index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# List of stub functions that need cleanup
stub_functions = [
    'GetStats',
    'InitPayments',
    'GetAllGames',
    'InitGameLabel',
    'GetFlags',
    'RequestingEnvironmentData',
    'InitPlayer'
]

# Pattern to match: function declaration followed by leftover code until next function
# We'll remove everything between the stub function and the next function declaration
for func in stub_functions:
    # Match the stub function and all code until the next function declaration
    pattern = rf'(function {func}\(\) {{ return Promise\.resolve\("no data"\); }})\s+(?:async )?function \w+'
    
    # Replace with just the stub function followed by newlines and the next function
    content = re.sub(
        pattern,
        r'\1\n\n',
        content,
        flags=re.DOTALL
    )
    
    # Also handle async function InitPlayer
    if func == 'InitPlayer':
        pattern = rf'(async function {func}\(\) {{ return Promise\.resolve\("no data"\); }};)\s+(?:async )?function \w+'
        content = re.sub(
            pattern,
            r'\1\n\n',
            content,
            flags=re.DOTALL
        )

# Also clean up any remaining orphaned code blocks
# Remove orphaned try-catch blocks, function Final() definitions, etc. that are not inside a function
# This is a more aggressive cleanup - remove code between stub functions and next function
content = re.sub(
    r'(function \w+\([^)]*\) \{ return Promise\.resolve\("no data"\); \})\s+(?:(?!function |async function )[^\n])+\n',
    r'\1\n\n',
    content,
    flags=re.MULTILINE
)

# More specific: remove orphaned code blocks after stub functions
# Match stub function, then any lines that don't start a new function, until we hit a function declaration
lines = content.split('\n')
cleaned_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    cleaned_lines.append(line)
    
    # If this is a stub function declaration
    if re.match(r'function \w+\([^)]*\) \{ return Promise\.resolve\("no data"\); \}', line.strip()) or \
       re.match(r'async function \w+\([^)]*\) \{ return Promise\.resolve\("no data"\); \};?', line.strip()):
        # Skip empty lines and then skip all non-function lines until we hit a function
        i += 1
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        
        # Skip all lines that are not function declarations until we find one
        while i < len(lines):
            stripped = lines[i].strip()
            # If it's a function declaration, break
            if re.match(r'(async )?function \w+', stripped):
                break
            # If it's just whitespace or closing braces from orphaned code, skip it
            if stripped == '' or stripped == '}' or stripped.startswith('//'):
                i += 1
                continue
            # Otherwise, it's orphaned code - skip it
            i += 1
    
    i += 1

content = '\n'.join(cleaned_lines)

# Write back
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Cleaned up leftover code after stub functions")

