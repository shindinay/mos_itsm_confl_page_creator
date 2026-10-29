# -*- coding: utf-8 -*-
"""Исправляет разорванные <a href="#..."> из TOC в published странице и перезаписывает."""
import json, re, os, sys
import ssl, urllib.request, urllib.error

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

CONFL = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator"

env = json.load(open(os.path.join(CONFL, ".env"), encoding="utf-8-sig"))
confl_base = env["CONFLUENCE_BASE_URL"].rstrip("/")
confl_token = env["CONFLUENCE_API_TOKEN"]

ctx = ssl._create_unverified_context()

def conf(method, path, data=None):
    hdrs = {"Authorization": "Bearer " + confl_token, "Accept": "application/json"}
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    url = confl_base + path
    raw = json.dumps(data).encode("utf-8") if isinstance(data, dict) else data
    req = urllib.request.Request(url, data=raw, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit("Confluence API %s %s HTTP %d: %s" % (method, path, e.code, e.read().decode("utf-8", errors="replace")[:300]))

# Загружаем текущую страницу с version
page = conf("GET", "/rest/api/content/738464895?expand=body.storage,version")
print("Page version:", page["version"]["number"])
body = page["body"]["storage"]["value"]

print("Original body length:", len(body))
a_hash = body.count('<a href="#')
print("Unclosed <a href='#'>:", a_hash)

# Конфлюенс TOC генерирует якоря как <a href="#ID">Text</a> — эти теги уже закрыты.
# Проблема: в нашем теле есть ссылки вида <a href="#..." без закрывающих </a>
# Причина: в шаблоне Confluence в разделе оглавления есть <a href="#..."> без </a>
# Конкретная проблема: шаблон содержит <a href="#..."> в тексте якорей оглавления
# Простое решение: добавляем </a> после каждой href="#" ссылки

# Находим все <a href="#..." и заменяем на <a href="#..."></a>
# Но только если закрывающего тега нет в пределах 500 символов
fixed_parts = []
last_end = 0

for m in re.finditer(r'<a href="([^"]*)"', body):
    href = m.group(1)
    after = m.end()
    close_idx = body.find('</a>', after)
    
    if close_idx == -1 or close_idx - after > 500:
        # Нет закрывающего тега — вставляем </a>
        fixed_parts.append(body[last_end:m.start()] + '<a href="' + href + '"></a>')
        last_end = after
    else:
        # Тег закрыт — пропускаем
        fixed_parts.append(body[last_end:close_idx + 4])
        last_end = close_idx + 4

fixed_parts.append(body[last_end:])
fixed_body = ''.join(fixed_parts)

# Проверяем баланс
a_open = len(re.findall(r'<a ', fixed_body))
a_close = fixed_body.count('</a>')
print("After fix: <a=" + str(a_open) + " </a>=" + str(a_close))

# Сохраняем
with open(os.path.join(CONFL, "temp", "page_body_738464895_fixed.html"), "w", encoding="utf-8") as f:
    f.write(fixed_body)

# Публикуем исправление
payload = {
    "id": "738464895",
    "type": "page",
    "version": {"number": page["version"]["number"] + 1},
    "body": {"storage": {"value": fixed_body, "representation": "storage"}},
}

result = conf("PUT", "/rest/api/content/738464895", payload)
print("Published v" + str(page["version"]["number"] + 1))
print("URL: " + confl_base + "/pages/viewpage.action?pageId=738464895")

# Финальная проверка
final = conf("GET", "/rest/api/content/738464895?expand=body.storage")
fb = final["body"]["storage"]["value"]
print("\nFinal check:")
print("  <a=" + str(len(re.findall(r'<a ', fb))) + " </a>=" + str(fb.count('</a>')))
print("  <p=" + str(fb.count('<p')) + " </p>=" + str(fb.count('</p>')))
print("  ac:link=" + str(fb.count('<ac:link')) + " </ac:link>=" + str(fb.count('</ac:link>')))
