# -*- coding: utf-8 -*-
import re

with open('temp/page_body_8170964_v12.html', 'r', encoding='utf-8') as f:
    body = f.read()

lines = body.split('\n')
print('Total lines:', len(lines))
print('Line 11 length:', len(lines[10]))
print('Line 11[2670:2720]:', repr(lines[10][2670:2720]))
print()

# Search for problematic patterns
# 1. Single quotes in attribute values (Confluence XHTML parser hates them)
single_q = re.findall(r'"[^"]*=[^>]*\'[^\']*\'[^"]*"', body)
print('Single quotes inside double-quoted attrs:', len(single_q))
for i, s in enumerate(single_q[:5]):
    print(f'  [{i}]: {s[:120]}')

# 2. Double quotes in single-quoted attribute values
double_q = re.findall(r"'[^']*=[^>]*\"[^\"]*\"[^']*'", body)
print('Double quotes inside single-quoted attrs:', len(double_q))
for i, s in enumerate(double_q[:5]):
    print(f'  [{i}]: {s[:120]}')

# 3. Find all <style> blocks
style_blocks = re.findall(r'<style[^>]*>.*?</style>', body, re.DOTALL)
print('Style blocks:', len(style_blocks))

# 4. Check for CDATA
cdata = re.findall(r'<!\[CDATA\[[^\]]*\]\]>', body)
print('CDATA blocks:', len(cdata))

# 5. Check for unescaped < inside <style> blocks
for i, sb in enumerate(style_blocks):
    # CDATA inside style is OK, but plain < inside style is not
    # Actually in Confluence, <style> content is CDATA by default
    pass

# 6. Print exact char at position 2687
if len(lines[10]) > 2687:
    pos = 2687
    start = max(0, pos - 20)
    end = min(len(lines[10]), pos + 20)
    print('Char at 2687:', repr(lines[10][pos]))
    print('Context:', repr(lines[10][start:end]))
