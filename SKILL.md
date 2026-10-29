---
name: mos_itsm_confl_page_creator
description: Создаёт страницу требований (REQ) в корпоративном Confluence ITPM (itpm-wiki.mos.ru) по корпоративному шаблону через REST API. Страница наполняется итогами работы соседних скиллов.
---

<!-- version: 1.1 — 27.10.2026. Исправлены пути: скрипт fetch_template.py лежит
     в scripts/ и читает .env (фолбэк skill_env.json); правила подстановки —
     manifesto/conf_variables_fulfilment_rules.md. -->

# ITPM Wiki REQ Page Creator

Скилл создаёт в Confluence страницу требований по корпоративному шаблону: получает тело шаблона, заполняет места для подстановки значениями от пользователя и публикует страницу через REST API.

Сервер — Confluence Data Center в корне домена (REST без префикса `/wiki`). Все шаги ниже проверены на реальном сервере; не заменяй их другими эндпоинтами без необходимости.

## Шаг 1 — Проверка доступов в Confluence и ITSM

Параметры лежат в `.env` рядом с SKILL.md:

- `CONFLUENCE_BASE_URL` — базовая ссылка
- `CONFLUENCE_API_TOKEN` — персональный токен доступа (PAT) как есть, без base64
- `ITPM_TEMPLATE_ID` — ID шаблона REQ
- `ITPM_SPACE_KEY` — пространство шаблона
- `ITPM_PARENT_PAGE_ID` (необязательно) — родительская страница по умолчанию

```bash
cd "<папка скилла>"
BASE=$(python -c "import json;print(json.load(open('skill_env.json',encoding='utf-8-sig'))['CONFLUENCE_BASE_URL'].rstrip('/'))")
TOKEN=$(python -c "import json;print(json.load(open('skill_env.json',encoding='utf-8-sig'))['CONFLUENCE_API_TOKEN'])")
AUTH="Authorization: Bearer $TOKEN"
curl -sS -m 15 -H "$AUTH" "$BASE/rest/api/user/current"
```

**Обязательно проверь авторизацию в Confluence.** Если в ответе `"type": "anonymous"` — токен не принят; остановись и попроси перевыпустить токен (аватар → Настройки → Персональные токены доступа) и вставить его в `skill_env.json` как есть. Этот сервер при неверном токене не возвращает 401, а молча отвечает как аноним — без этой проверки всё выглядит «почти работающим».

**Обязательно проверь авторизацию ITSM**. Используй Authorization: Bearer <token> + X-4me-Account: `ITPM_SPACE_KEY`

## Шаг 2 — Выясни у пользователя ряд параметров и запомни их

Выясни:
- **request_id** — заголовок новой страницы (из запроса пользователя).


## Шаг 3 — Собери параметры страницы

- **title** — заголовок новой страницы (из запроса пользователя).
- **space key** — где создать страницу; из запроса, иначе спроси. (Пространство `DIT4ME` — это источник шаблона, страницу туда класть не обязательно.)
- **parent page ID** — из запроса, иначе `ITPM_PARENT_PAGE_ID`, иначе без родителя.
- **значения для заполнения** — лучше одним JSON-объектом. Если каких-то значений не хватает, задай недостающие вопросы одним сообщением, а не по одному.

Не задавай вопросов, если всё уже есть в запросе или в `skill_env.json` или в файле `.env`.

## Шаг 4 — Получи актуальный шаблон-трафарет для заполнения

REST-эндпоинты шаблонов (`/rest/api/template/...`) на сервере отключены — не используй их. Тело шаблона извлекается из страницы-просмотра готовым скриптом:

```bash
cd "<папка скилла>"
python scripts/fetch_template.py
```

Скрипт читает `ITPM_TEMPLATE_ID` и `ITPM_SPACE_KEY` из `skill_env.json` (можно передать и аргументами), скачивает `pages/templates2/viewpagetemplate.action`, извлекает сбалансированный блок `wiki-content view-template` и сохраняет его в `template_body.html`. В stdout он печатает список мест для заполнения.

## Шаг 5 — Подготовь страницу к созданию

Места для заполнения в шаблоне — это макросы Placeholder, в HTML они выглядят так:

```html
<span class="template-variable">`{{переменная}}`</span>
```
Замена: для каждой переменной подставь значение пользователя. Пример замены одного места:
Правила подстановки - СТРОГО из файла `manifesto/conf_variables_fulfilment_rules.md`

Значения для переменных получишь в результате применения скиллов:
- mos_itsm_automation_rule_descriptor
- mos-itsm-get-obj-structure
- mos-itsm-ui-extension_descriptor

Правила:

- Текст пользователя вставляй валидным XHTML: экранируй `&`, `<`, `>`; переносы строк оформляй абзацами `<p>...</p>`.
- Внешние ссылки вставляй только как `<ac:link><ri:url ri:value="URL" /></ac:link>` — голый `<a href="URL">` вызывает HTTP 500 (ClassCastException на ResourceIdentifier).
- Автор требования вставляется макросом пользователя — в storage-формате: `<ac:structured-macro ac:name="profile"><ac:parameter ac:name="user"><ri:user ri:userkey="USERKEY" /></ac:parameter></ac:structured-macro>`. Строка username или обёртка `<ac:link>` в параметре дают HTTP 500 — нужен именно голый `<ri:user>` с **userkey** (получить через `/rest/api/user/current` для себя или `/rest/api/user?username=...` для другого). Если userkey получить нельзя, оставь плейсхолдер и отметь это в итоге.
- Незаполненные места не выдумывай: сохрани их как есть и перечисли пользователю в итоге.

## Шаг 6 — Создай страницу

Только v1 API (`POST /rest/api/content`); v2 на сервере недоступен:

```bash
python - <<'EOF'
import json, os
payload = {
    "type": "page",
    "title": os.environ["PAGE_TITLE"],
    "space": {"key": os.environ["SPACE_KEY"]},
    "body": {"storage": {"value": open("page_body.html", encoding="utf-8").read(),
                          "representation": "storage"}},
}
if os.environ.get("PARENT_ID"):
    payload["ancestors"] = [{"id": os.environ["PARENT_ID"]}]
open("payload.json", "w", encoding="utf-8").write(json.dumps(payload))
EOF
PAGE_TITLE="..." SPACE_KEY="..." PARENT_ID="..." python - <<'EOF'
import json, urllib.request, os
env = json.load(open("skill_env.json", encoding="utf-8-sig"))
base = env["CONFLUENCE_BASE_URL"].rstrip("/")
req = urllib.request.Request(base + "/rest/api/content",
    data=open("payload.json","rb").read(),
    headers={"Authorization": "Bearer " + env["CONFLUENCE_API_TOKEN"],
             "Content-Type": "application/json"}, method="POST")
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
print(resp["id"], resp["_links"]["base"] + resp["_links"]["webui"])
EOF
```

Проверь ответ: HTTP 200 содержит `id` и `_links.webui`. 403 или «permissionViolation» — у токена нет прав на запись в это пространство: сообщи пользователю, не повторяй запрос.

## Шаг 7 — Верни результат

Сообщи пользователю: ссылку на страницу (из `_links.base` + `_links.webui`), заголовок, ID и список незаполненных мест в шаблоне (если остались). При ошибке — точный текст ответа сервера и что исправить.