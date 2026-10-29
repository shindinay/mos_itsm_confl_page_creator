# -*- coding: utf-8 -*-
"""Загружает тело шаблона Confluence и сохраняет его в storage-совместимом HTML.

REST-эндпоинты шаблонов (/rest/api/template/...) на сервере itpm-wiki.mos.ru
отключены администраторами, поэтому тело берётся из страницы-просмотра шаблона
(pages/templates2/viewpagetemplate.action) — из блока <div class="wiki-content
view-template">. Извлекается сбалансированный блок вместе с вложенными div.

Использование:
  python fetch_template.py [template_id] [space_key]

template_id и space_key берутся из .env (JSON) скилла, если не переданы явно;
фолбэк — skill_env.json.
Результат: template_body.html рядом со скриптом; в stdout — краткая сводка.
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


def extract_view_template_div(html):
    """Возвращает внутренности <div class="wiki-content view-template">...</div>.

    Ищет закрывающий div балансировкой: вложенные <div> увеличивают счётчик,
    поэтому блок корректно обрезается на своём закрывающем теге, а не раньше.
    """
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
    template_id = sys.argv[1] if len(sys.argv) > 1 else env.get("ITPM_TEMPLATE_ID", "")
    space_key = sys.argv[2] if len(sys.argv) > 2 else env.get("ITPM_SPACE_KEY", "")
    if not template_id or not space_key:
        raise SystemExit("Нужны template_id и space_key (аргументы или .env)")

    url = (f"{base}/pages/templates2/viewpagetemplate.action"
           f"?entityId={template_id}&key={space_key}")
    html = fetch(url, token)

    m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = m.group(1).strip() if m else ""
    body = extract_view_template_div(html)

    out = os.path.join(SKILL_DIR, "template_body.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)

    # Места для заполнения: макрос Placeholder рендерится как text-placeholder,
    # плюс возможные явные {{var}} (в этом шаблоне {{...}} встречаются только
    # внутри текстов-примеров — их заменять не нужно).
    placeholders = re.findall(r'<span class="text-placeholder">(.*?)</span>', body, re.S)
    clean = []
    for p in placeholders:
        t = re.sub(r"<[^>]+>", "", p).strip()
        if t:
            clean.append(t)

    print(f"Заголовок страницы-просмотра: {title[:100]}")
    print(f"Тело шаблона сохранено: {out} ({len(body)} символов)")
    print(f"Мест для заполнения ({len(clean)}):")
    for t in clean:
        print(f"  - {t[:90]}")


if __name__ == "__main__":
    main()
