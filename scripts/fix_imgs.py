#!/usr/bin/env python3
"""Fix <img> tags in template_body.html to be self-closing for Confluence storage format."""

import re

with open("template_body.html", "r", encoding="utf-8") as f:
    body = f.read()

print(f"Original body: {len(body)} bytes")

# Count original img tags
original_imgs = re.findall(r'<img\b', body)
print(f"Original img tags: {len(original_imgs)}")

# Strategy: Use a state machine to find <img...> and fix them
# This avoids regex issues with complex attribute values

result = []
i = 0
while i < len(body):
    if body[i] == '<' and body[i+1:i+4].lower() == 'img':
        # Found potential <img tag - find the closing >
        j = body.find('>', i)
        if j == -1:
            result.append(body[i:])
            break
        
        tag = body[i:j+1]
        # Check if already self-closing
        if not tag.rstrip().endswith('/}'):
            # Remove trailing > and add />
            tag = tag.rstrip()[:-1] + '/>'
        
        result.append(tag)
        i = j + 1
    else:
        result.append(body[i])
        i += 1

fixed_body = ''.join(result)

# Count fixed img tags
fixed_imgs = re.findall(r'<img\b[^>]*>', fixed_body)
print(f"Fixed img tags: {len(fixed_imgs)}")
for img in fixed_imgs:
    ends = img.rstrip().endswith('/>')
    print(f"  self-closing={ends}: {img[:120]}")

with open("page_body_8170964_final.html", "w", encoding="utf-8") as f:
    f.write(fixed_body)

print(f"Fixed body: {len(fixed_body)} bytes")
