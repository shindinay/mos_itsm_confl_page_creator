#!/usr/bin/env python3
"""Проверка созданной страницы Confluence: ссылки, нумерация, плейсхолдеры."""
import json
import re
import urllib.request
import urllib.error

ENV_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
PAGE_ID = "738465719"

with open(ENV_FILE, encoding="utf-8-sig") as f:
    env = json.load(f)

base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]

# Fetch page body
url = f"{base}/rest/api/content/{PAGE_ID}?expand=body.storage"
req = urllib.request.Request(url, headers={
    "Authorization": "Bearer " + token,
    "Accept": "application/json",
})
with urllib.request.urlopen(req, timeout=30) as resp:
    page = json.loads(resp.read().decode("utf-8"))

body = page["body"]["storage"]["value"]
print(f"Страница {PAGE_ID} загружена ({len(body)} символов)")

# Check 1: ac:link tags with empty ac:plain-text-body
print("\n=== Проверка 1: ac:link с пустым текстом ===")
empty_links = []
for m in re.finditer(r'<ac:link[^>]*>(.*?)</ac:link>', body, re.DOTALL):
    link_body = m.group(1)
    plain_match = re.search(r'<ac:plain-text-body>\s*(.*?)\s*</ac:plain-text-body>', link_body, re.DOTALL)
    if not plain_match:
        empty_links.append({"link_id": re.search(r'ref="(\d+)"', m.group(1))})
    elif not plain_match.group(1).strip():
        empty_links.append({"match": m.group(0)[:200]})

if empty_links:
    print(f"НАЙДЕНО {len(empty_links)} пустых ссылок:")
    for el in empty_links[:10]:
        print(f"  {el}")
else:
    print("OK: все ac:link имеют непустой текст")

# Check 2: numhead-number in headings
print("\n=== Проверка 2: нумерация заголовков ===")
headings = re.findall(r'<h[1-6][^>]*class="[^"]*numhead-number[^"]*"[^>]*>(.*?)</h\1>', body, re.DOTALL)
if not headings:
    # Try alternate pattern
    headings = re.findall(r'<h[1-6][^>]*>.*?numhead-number[^>]*>.*?</h[1-6]>', body, re.DOTALL)

# Better: find all h tags with numhead-number
numhead_count = len(re.findall(r'numhead-number', body))
h_tags = re.findall(r'<h([1-6])[^>]*>', body)
print(f"numhead-number встречается {numhead_count} раз")
print(f"Всего заголовков h1-h6: {len(h_tags)}")

# Check 3: @user mentions (profile macros)
print("\n=== Проверка 3: упоминания авторов ===")
profile_macros = re.findall(r'<ac:structured-macro[^>]*ac:name="profile"[^>]*>.*?</ac:structured-macro>', body, re.DOTALL)
if profile_macros:
    print(f"НАЙДЕНО profile macro: {len(profile_macros)}")
    for pm in profile_macros:
        uk = re.search(r'ri:userkey="([^"]+)"', pm)
        if uk:
            print(f"  userkey={uk.group(1)}")
else:
    print("Нет profile macro в странице")

# Check 4: unfilled placeholders (**...)
print("\n=== Проверка 4: незаполненные плейсхолдеры (**) ===")
placeholders = re.findall(r'\*\*[\w_]+\*\*', body)
if placeholders:
    unique = set(placeholders)
    print(f"НАЙДЕНО незаполненных плейсхолдеров ({len(unique)}):")
    for p in sorted(unique):
        print(f"  - {p}")
else:
    print("OK: все плейсхолдеры заполнены")

# Check 5: Table of contents
print("\n=== Проверка 5: Оглавление ===")
toc = re.findall(r"href='(#[^']+)'", body)
if toc:
    print(f"Ссылок в оглавлении: {len(toc)}")
    for t in toc[:15]:
        print(f"  {t}")

# Check 6: Verify task sections
print("\n=== Проверка 6: Разделы задач ===")
task_h2 = re.findall(r'<h2[^>]*>.*?</h2>', body, re.DOTALL)
print(f"Заголовков h2 найдено: {len(task_h2)}")
for h in task_h2:
    # Extract text
    text = re.sub(r'<[^>]+>', '', h).strip()
    if text:
        print(f"  - {text[:100]}")

# Check 7: Verify automation rule links
print("\n=== Проверка 7: Ссылки на правила автоматизации ===")
ar_links = re.findall(r'href="https://itsm\.itsm-qa\.mos\.ru/automation_rules/(\d+)"', body)
print(f"Ссылок на правила автоматизации: {len(ar_links)}")
for al in sorted(set(ar_links)):
    print(f"  - {al}")

print("\nПроверка завершена.")
