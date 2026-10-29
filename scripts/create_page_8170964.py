#!/usr/bin/env python3
"""Создание страницы Confluence REQ для запроса 8170964 (шаблон 56363) — фикс XHTML."""
import json
import re
import os
import html
import urllib.request
import urllib.error

# --- Config ---
ENV_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
TEMPLATE_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\template_body.html"
PARENT_ID = "735534111"
OUTPUT_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\page_body_8170964.html"
PAYLOAD_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\temp\payload_8170964.json"

env = json.load(open(ENV_FILE, encoding="utf-8-sig"))
base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]
space_key = "DIT4ME"
userkey = "2c98d8026e1c34cb016e45ea6c064b40"

# --- Данные запроса 8170964 (из request_vars_8170964_20261028_134841.json) ---
REQ_ID = "8170964"
REQ_URI = "https://itsm.itsm-qa.mos.ru/requests/8170964"
REQ_SUBJECT = "Сбой в задаче Автомат. блокировка соглашений и КЕ. Предоставление клиентского пакета обслуживания (Автогенерация)"
REQ_REQUESTED_FOR = "Служебная УЗ"
REQ_CREATED_AT = "2026-10-28T13:41:19+03:00"
REQ_FIRST_COMMENT = "2026-10-28T13:41:19+03:00 | Служебная УЗ: Создано для задачи <task#8605352> рабочего процесса <workflow#628657>"

# --- Описания (desc_*.md) ---
uiext_14567_path = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_UI-extension_creator\artifact\desc_14567.md"
RULE_DESC_ROOT = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\artifact"

# Правила: (id, имя, объект: tpl|4313|7411|31693|31697)
RULES = [
    (10249331, "Закрыть запрос если переоткрыли", "tpl"),
    (10249443, "Создать запрос в Р-Сервис. Заказ демо-стенда (ApiGate 1.0)", "tpl"),
    (13553013, "Завершить после решения от р-сервис", "tpl"),
    (1914157, "Генерация задачи на обработку", "4313"),
    (1914235, "Возврат статуса зарегистрировано", "4313"),
    (1991869, "Автозавершение", "4313"),
    (2655131, "Завершить при назначении", "7411"),
    (13934317, "Запуск таймера сбоя", "31693"),
    (13934321, "Сбой обработки", "31693"),
    (13935097, "Проброс коммента в запрос, закрытие РП и запроса", "31697"),
]

TASK_NAMES = {
    4313: "Мониторинг сбоев роботизации. Команда \"ДИТ.MOS.ITSM.Администраторы\"",
    7411: "Балансировщик статусов",
    31693: "Ожидание ответа сервиса. Предоставление доступа к демо стенду",
    31697: "Авто-закрытие РП. Предоставление доступа к демо стенду",
}

QA_WEB = "https://itsm.itsm-qa.mos.ru"


def read_md(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return "(файл не найден)"


TABLE_TAG_RE = re.compile(r'</?(?:table|tbody|thead|colgroup|col|tr|th|td)\b[^>]*>?')


def is_table_tag_line(s):
    """Строка содержит теги таблицы (открывающие/закрывающие)."""
    return bool(re.search(r'</?\s*(?:table|tbody|thead|colgroup|col|tr|th|td)\b', s))


def clean_and_escape(s):
    """Убрать 4me-теги <c #...>, экранировать XHTML, преобразовать **bold** и __italic__."""
    s = re.sub(r'<c\s*#[0-9a-fA-F]+\s*>', '', s)
    s = s.replace('</c>', '')
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'__(.+?)__', r'<em>\1</em>', s)
    return s


def md_block_to_xhtml(md_text):
    """Конвертирует markdown описания (H1/H2/H3, построчные HTML-таблицы, абзацы)
    в XHTML-фрагмент для storage-формата Confluence.

    Строки с тегами таблицы проходят как есть; текстовые строки внутри таблицы
    вставляются без <p> (это содержимое ячеек); текстовые строки вне таблиц
    собираются в абзацы <p>."""
    out = []
    para = []
    inside_table = False

    def flush():
        if para:
            text = " ".join(x for x in para if x).strip()
            para.clear()
            if text:
                out.append('<p>' + text + '</p>')

    for line in md_text.split("\n"):
        s = line.strip()
        if not s:
            flush()
            continue
        if s.startswith('### '):
            flush()
            out.append('<h6>' + clean_and_escape(s[4:]) + '</h6>')
            continue
        if s.startswith('## '):
            flush()
            out.append('<h5>' + clean_and_escape(s[3:]) + '</h5>')
            continue
        if s.startswith('# '):
            flush()
            out.append('<h4>' + clean_and_escape(s[2:]) + '</h4>')
            continue
        if is_table_tag_line(s):
            flush()
            if '<table' in s and '</table>' in s:
                pass  # самодостаточная строка, состояние не меняется
            elif '<table' in s:
                inside_table = True
            elif '</table>' in s:
                inside_table = False
            out.append(s)
            continue
        # текстовая строка
        text = clean_and_escape(s)
        if inside_table:
            out.append(text)
        else:
            para.append(text)
    flush()
    return "\n".join(out)


def rule_summary(rid):
    """Первый абзац раздела «Описание» из desc_<id>.md (до 300 символов)."""
    path = os.path.join(RULE_DESC_ROOT, f"desc_{rid}.md")
    text = read_md(path)
    m = re.search(r'<c #0f1115>(.+?)</c>', text, re.DOTALL)
    if not m:
        m = re.search(r'\*\*Описание\*\*\s*\n\s*\n?(.+?)(?=\n\n|\*\*История)', text, re.DOTALL)
    if m:
        s = m.group(1).strip().replace("\n", " ")
        s = re.sub(r'<[^>]+>', '', s)  # убрать html-теги для краткой сводки
        return s[:300]
    return "описание не сгенерировано"


# --- Build content ---
uiext_14567_md = read_md(uiext_14567_path)
req_ui_ext_ai_desc = md_block_to_xhtml(uiext_14567_md)

# 8.1.2 — правила шаблона запроса: сводка + ссылки
tpl_rules = [r for r in RULES if r[2] == "tpl"]
req_ar_desc_template = '<p>3 правила автоматизации на шаблоне запроса:</p><ul>' + "".join(
    f'<li>ID {rid}: {html.escape(name)} — {html.escape(rule_summary(rid))[:300]} <a href="{QA_WEB}/automation_rules/{rid}">{QA_WEB}/automation_rules/{rid}</a></li>'
    for rid, name, _ in tpl_rules
) + "</ul>"

# 8.2 — РП 15785: без UI-расширений и без правил на уровне РП
wf_ui_ext_desc = '<p>Отсутствует (UI-расширений на уровне рабочего процесса 15785 нет)</p>'
wf_ar_desc = '<p>Отсутствуют (правил автоматизации на уровне рабочего процесса 15785 нет)</p>'

# 8.3 — шаблоны задач
task_template_name = "; ".join(f"{tid}: {TASK_NAMES[tid]}" for tid in (4313, 7411, 31693, 31697))

task_rules_html = ['<p>Сводка по 7 правилам шаблонов задач рабочего процесса 15785:</p>']
for tid in (4313, 7411, 31693, 31697):
    rules_of_task = [r for r in RULES if r[2] == str(tid)]
    task_rules_html.append(f'<p><strong>Задача {tid} — {html.escape(TASK_NAMES[tid])} ({len(rules_of_task)} правил):</strong></p>')
    task_rules_html.append('<ul>')
    for rid, name, _ in rules_of_task:
        link = f"{QA_WEB}/automation_rules/{rid}"
        task_rules_html.append(
            f'<li>ID {rid}: {html.escape(name)} — {html.escape(rule_summary(rid))[:300]} <a href="{link}">{link}</a></li>'
        )
    task_rules_html.append('</ul>')
task_rules_html = "".join(task_rules_html)

# --- Read template and make img tags XHTML-compliant ---
with open(TEMPLATE_FILE, encoding="utf-8") as f:
    body = f.read()

body = re.sub(r'<img([^>]*)>', lambda m: '<img' + m.group(1).rstrip() + '/>', body)

# Replace author with profile macro
author_macro = ('<ac:structured-macro ac:name="profile"><ac:parameter ac:name="user">'
                '<ri:user ri:userkey="' + userkey + '" /></ac:parameter></ac:structured-macro>')
body = re.sub(
    r'(<td class="highlight-#f4f5f7 confluenceTd"[^>]*><strong[^>]*>Автор</strong>.*?<img[^>]*/></span></em></span></span></p></td>)',
    '<td class="highlight-#f4f5f7 confluenceTd"><p>' + author_macro + '</p></td>',
    body, count=1, flags=re.DOTALL
)

# Fix enableNumbering in headings
body = re.sub(
    r'<h1[^>]*id="[^"]*"[^>]*><span[^>]*>2\. </span>\{[^}]*enableNumbering[^}]*\}</h1>',
    '<h1><span class="numhead-number">2. </span>Общие сведения</h1>', body, count=1
)
body = re.sub(
    r'<li><a href="[^"]*enableNumbering[^"]*">2\.\s*\{[^}]*enableNumbering[^}]*\}</a></li>',
    '<li><a href="#Общиесведения">2. Общие сведения</a></li>', body, count=1
)

# --- Simple text replacements (по одному вхождению) ---
simple_replacements = [
    ("rfc_id", REQ_ID),
    ("req_created_at", REQ_CREATED_AT),
    ("req_requested_for", REQ_REQUESTED_FOR),
    ("req_subject", REQ_SUBJECT),
    ("req_id", REQ_ID),
    ("req_template_subj", "МосИТСМ. Предоставление доступа к демо стенду"),
    ("task_template_name", task_template_name),
]
for var_name, value in simple_replacements:
    pattern = r'<input[^>]*name="variableValues\.' + var_name + r'"[^>]*/?>\s*<span class="templateparameter">\([^)]*\)</span>'
    body, n = re.subn(pattern, html.escape(value), body, count=1)
    if n == 0:
        print(f"WARN: placeholder {var_name} not replaced")

# --- req_template_account: img-плейсхолдер -> текст ---
pattern = r'<img[^>]*template-variable\?name=req_template_account[^>]*/>'
body, n = re.subn(pattern, html.escape("Каталог услуг Правительства Москвы (itsm)"), body, count=1)
if n == 0:
    print("WARN: req_template_account not replaced")

# --- req_uri: ссылка на запрос (ac:link по правилам SKILL) ---
req_uri_html = (f'<ac:link><ri:url ri:value="{REQ_URI}" /></ac:link>'
                f' ({html.escape(REQ_URI)})')
pattern = r'<img[^>]*src="[^"]*template-variable\?name=req_uri[^"]*"[^>]*/>'
body, n = re.subn(pattern, req_uri_html, body, count=1)
if n == 0:
    print("WARN: req_uri not replaced")

# --- req_first_comment: многострочный текст постановки ---
first_comment_html = html.escape(REQ_FIRST_COMMENT)
pattern = r'<input[^>]*name="variableValues\.req_first_comment"[^>]*/?>\s*<span class="templateparameter">\([^)]*\)</span>'
body, n = re.subn(pattern, first_comment_html, body, count=1)
if n == 0:
    print("WARN: req_first_comment not replaced")

# --- Описания расширения UI и правил (многострочные HTML) ---
replacements_html = [
    ("req_ui_ext_ai_desc", req_ui_ext_ai_desc),
    ("req_template_automation_rule_ai_description", req_ar_desc_template),
    ("wf_ui_ext_desc", wf_ui_ext_desc),
    ("wf_ar_desc", wf_ar_desc),
]
for var_name, value in replacements_html:
    pattern = r'<input[^>]*name="variableValues\.' + var_name + r'"[^>]*/?>\s*<span class="templateparameter">\([^)]*\)</span>'
    body, n = re.subn(pattern, value, body, count=1)
    if n == 0:
        print(f"WARN: {var_name} not replaced")

# --- Заполнить таблицу параметров шаблона (8.1) ---
body = re.sub(
    r'(<td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><p>14567: Предоставление демо стенда (вкладка «Информация», <a href="' + QA_WEB + '/ui_extensions/14567">' + QA_WEB + '/ui_extensions/14567</a>)</p></td>',
    body, count=1
)
body = re.sub(
    r'(<td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd"><p>10 правил (3 на шаблоне, 7 на задачах — см. разделы 8.1.2 и 8.3.2)</p></td>',
    body, count=1
)
body = re.sub(
    r'(<td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd"><p>15785: МосИТСМ. Предоставление доступа к демо стенду (<a href="' + QA_WEB + '/workflow_templates/15785">' + QA_WEB + '/workflow_templates/15785</a>)</p></td>',
    body, count=1
)

# --- 8.3.1 (Требования к Расширению UI на задачах) — расширений нет ---
body = re.sub(
    r'(<h3 id="[^"]*">8\.3\.1\. </span>Требования к Расширению UI</h3>)',
    r'\1\n<p>Отсутствуют (UI-расширений у шаблонов задач 4313, 7411, 31693, 31697 нет)</p>',
    body, count=1
)

# --- 8.3.2 — сводка по правилам задач ---
body = re.sub(
    r'(<h3 id="[^"]*">8\.3\.2\. </span><span>Требования к правилам автоматизации</span></h3>)',
    r'\1\n' + task_rules_html,
    body, count=1
)

# --- Write page body ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(body)
print("Page body written:", OUTPUT_FILE, len(body), "chars")

# --- Create page ---
PAGE_TITLE = f"{REQ_ID}-МосИТСМ. Предоставление доступа к демо стенду - Предоставление доступа к демо стенду"
payload = {
    "type": "page",
    "title": PAGE_TITLE,
    "space": {"key": space_key},
    "body": {"storage": {"value": body, "representation": "storage"}},
    "ancestors": [{"id": PARENT_ID}],
}
os.makedirs(os.path.dirname(PAYLOAD_FILE), exist_ok=True)
with open(PAYLOAD_FILE, "w", encoding="utf-8") as f:
    json.dump(payload, f)

req = urllib.request.Request(
    base + "/rest/api/content",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    method="POST",
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    print("SUCCESS! Page ID:", result["id"])
    print("Page URL:", result["_links"]["base"] + result["_links"]["webui"])
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode("utf-8")[:500])
except Exception as e:
    print("Error:", e)
