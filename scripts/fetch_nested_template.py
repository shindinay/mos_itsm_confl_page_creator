#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Загружает тело шаблона Confluence по ID.

Испольуется для подстановки вложенных шаблонов:
  python fetch_nested_template.py 736854040

Результат: HTML-тело шаблона сохраняется во временный файл.
Стандарт: https://itpm-wiki.mos.ru/pages/templates2/viewpagetemplate.action?entityId={{id}}&key=DIT4ME
"""
import json
import os
import re
import sys
import urllib.request

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    for name in (".env", "skill_env.json"):
        path = os.path.join(SKILL_DIR, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8-sig") as f:
                return json.load(f)
    raise SystemExit(f"Не найден файл окружения (.env или skill_env.json) в {SKILL_DIR}")


def fetch(url, token):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_template_body(html):
    """Извлекает содержимое <div class="wiki-content view-template">...</div>."""
    marker = '<div class="wiki-content view-template"'
    start = html.find(marker)
    if start == -1:
        raise SystemExit("Блок wiki-content view-template не найден — шаблон недоступен или ссылка неверна")
    body_start = html.find(">", start) + 1
    depth = 1
    pos = body_start
    tag_re = re.compile(r"<(/?)div\b[^>]*>", re.I)
    for m in tag_re.finditer(html, body_start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            pos = m.start()
            break
    if depth != 0:
        raise SystemExit("Не удалось найти закрывающий тег блока шаблона")
    return html[body_start:pos].strip()


def main():
    env = load_env()
    token = env["CONFLUENCE_API_TOKEN"]
    base = env["CONFLUENCE_BASE_URL"].rstrip("/")
    template_id = sys.argv[1] if len(sys.argv) > 1 else ""
    if not template_id:
        raise SystemExit("Нужен template_id (аргумент)")

    url = f"{base}/pages/templates2/viewpagetemplate.action?entityId={template_id}&key=DIT4ME"
    html = fetch(url, token)

    m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = m.group(1).strip() if m else ""
    body = extract_template_body(html)

    print(f"Заголовок: {title[:100]}")
    print(f"Длина тела: {len(body)} символов")
    # Выводим тело в stdout
    print("---BODY_START---")
    print(body)
    print("---BODY_END---")


if __name__ == "__main__":
    main()
