#!/usr/bin/env python3
"""Диагностика: показать структуру страницы 738465719."""
import json
import re
import urllib.request

ENV_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
PAGE_ID = "738465719"

with open(ENV_FILE, encoding="utf-8-sig") as f:
    env = json.load(f)

base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]

url = f"{base}/rest/api/content/{PAGE_ID}?expand=body.storage"
req = urllib.request.Request(url, headers={
    "Authorization": "Bearer " + token,
    "Accept": "application/json",
})
with urllib.request.urlopen(req, timeout=30) as resp:
    page = json.loads(resp.read().decode("utf-8"))

body = page["body"]["storage"]["value"]

# Find all h tags
print("=== Все заголовки ===")
for m in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', body, re.DOTALL):
    hlevel = m.group(1)
    hcontent = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    print(f"  H{hlevel}: {hcontent[:120]}")

print("\n=== Плейсхолдеры **...** ===")
for m in re.finditer(r'\*\*[\w_]+\*\*', body):
    context_start = max(0, m.start() - 50)
    context = body[context_start:m.end()+30]
    clean = re.sub(r'<[^>]+>', '', context).strip()
    print(f"  [{m.group()}] context: {clean[:100]}")

print("\n=== Ищем div с innerCell (структура) ===")
for m in re.finditer(r'<div class="innerCell">', body):
    start = m.start()
    # Find next few lines
    chunk = body[start:start+500]
    print(f"  at {start}: {re.sub(r'<[^>]+>', '', chunk)[:200]}")
    print("  ---")

print("\n=== Section 9 content (raw) ===")
idx9 = body.find('id="DIT4ME-Требованиякобъектамсистемы"')
if idx9 > 0:
    chunk = body[idx9:idx9+3000]
    print(chunk[:3000])
