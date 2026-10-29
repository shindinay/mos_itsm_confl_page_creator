# -*- coding: utf-8 -*-
"""Создаёт страницу Confluence v2.2 (28.10.2026) для шаблона 56363, RFC 8170964.
Корректировки: (1) автор @-упоминание, (2) оглавление не трогать, (3) все ac:link с текстом, (4) структура правил."""
import json, re, os, sys
import xml.etree.ElementTree as ET
import ssl, urllib.request, urllib.error

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

CONFL = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator"
SKILL = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_get_obj_structure"
AR_DESC = CONFL.replace("mos_itsm_confl_page_creator", "mos_itsm_automation_rule_descriptor") + "/artifact"
UI_DESC = CONFL.replace("mos_itsm_confl_page_creator", "mos_itsm_UI-extension_creator") + "/artifact"

env = json.load(open(os.path.join(CONFL, ".env"), encoding="utf-8-sig"))
itsm_token = env["MOSITSM_PERS_TOKEN_QA"]
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
        raise SystemExit("Confluence API %s %s HTTP %d: %s" % (method, path, e.code, e.read().decode("utf-8", errors="replace")[:200]))

def itsm_get(endpoint):
    url = "https://api.itsm-qa.mos.ru/v1/" + endpoint
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + itsm_token,
              "X-4me-Account": "itsm", "Accept": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def card_link(rid):
    return '<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/automation_rules/%s" /><ac:plain-text-body>Карточка правила %s</ac:plain-text-body></ac:link>' % (rid, rid)

# === Load data ===
rv = json.load(open(os.path.join(SKILL, "artifact", "request_vars_8170964_20261028_134438.json"), encoding="utf-8"))["request_variables"]
tpl = open(os.path.join(CONFL, "template_body.html"), encoding="utf-8").read()
st = json.load(open(os.path.join(SKILL, "artifact", "structure_56363_20261028_134057.json"), encoding="utf-8"))

rvs = {
    "id": str(rv["request.id"]),
    "uri": rv["request.uri"],
    "subject": rv["request.subject"],
    "requested_for": rv["request.requested_for"],
    "created_at": rv["request.created_at"],
    "first_comment": rv["request.notes[first]"],
}
tpl_subj = st["request_template"]["subject"]
tpl_account = "Каталог услуг Правительства Москвы (itsm)"

# Load rules
ALL_RULES = [
    ("10249331", "Закрыть запрос если переоткрыти"),
    ("10249443", "Создать запрос в Р-Сервис. Заказ демо-стенда (ApiGate 1.0)"),
    ("13553013", "Завершить после решения от р-сервис"),
    ("1914157", "Генерация задачи на обработку"),
    ("1914235", "Возврат статуса зарегистрировано"),
    ("1991869", "Автозавершение"),
    ("2655131", "Завершить при назначении"),
    ("13934317", "Запуск таймера сбоя"),
    ("13934321", "Сбой обработки"),
    ("13935097", "Проброс коммента в запрос, закрытие РП и запроса"),
]
rules_data = []
for rid, rname in ALL_RULES:
    r = itsm_get("automation_rules/" + rid)
    expr_text = r.get("expressions", "") or ""
    expressions = []
    for line in expr_text.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        expressions.append((name.strip(), value.strip()))
    act_text = r.get("actions", "") or ""
    actions = []
    for line in act_text.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        actions.append((name.strip(), value.strip()))
    cond = (r.get("condition", "") or "").strip()
    rules_data.append({"id": rid, "name": rname, "trigger": r.get("trigger", ""),
                       "condition": cond, "expressions": expressions, "actions": actions})

template_rules = rules_data[:3]
task_rules = rules_data[3:]

TASKS = [
    {"id": "4313", "name": "Мониторинг сбоев роботизации. Команда \"ДИТ.MOS.ITSM.Администраторы\"", "rule_ids": ["1914157", "1914235", "1991869"]},
    {"id": "7411", "name": "Балансировщик статусов", "rule_ids": ["2655131"]},
    {"id": "31693", "name": "Ожидание ответа сервиса. Предоставление доступа к демо стенду", "rule_ids": ["13934317", "13934321"]},
    {"id": "31697", "name": "Авто-закрытие РП. Предоставление доступа к демо стенду", "rule_ids": ["13935097"]},
]

# === Helper functions ===
def settings_table(rule):
    rows = []
    rows.append("<table><tbody>")
    rows.append("<tr><td><p><strong>Триггер</strong></p></td><td><p>%s</p></td></tr>" % esc(rule["trigger"]))
    rows.append("<tr><td><p><strong>Условие</strong></p></td><td><p>%s</p></td></tr>" % esc(rule["condition"]))
    rows.append("</tbody></table>")
    return "\n".join(rows)

def expressions_table(rule):
    rows = ["<table><tbody>"]
    rows.append("<tr><th><p><strong>Имя выражения</strong></p></th><th><p><strong>Логика</strong></p></th></tr>")
    for name, value in rule["expressions"]:
        rows.append("<tr><td><p>%s</p></td><td><p>%s</p></td></tr>" % (esc(name), esc(value)))
    rows.append("</tbody></table>")
    return "\n".join(rows)

def actions_table(rule):
    rows = ["<table><tbody>"]
    rows.append("<tr><th><p><strong>Действие</strong></p></th><th><p><strong>Описание</strong></p></th></tr>")
    for atype, avalue in rule["actions"]:
        rows.append("<tr><td><p>%s</p></td><td><p>%s</p></td></tr>" % (esc(atype), esc(avalue)))
    rows.append("</tbody></table>")
    return "\n".join(rows)

# === Author @-mention ===
PROFILE_AT = '<ac:link><ac:link-body><ri:user ri:userkey="2c98d8026e1c34cb016e45ea6c064b40" /></ac:link-body></ac:link>'
AUTH_LINK = '<a href="%s">RFC %s</a>' % (rvs["uri"], rvs["id"])

body = tpl

def replace_input(name, value):
    global body
    pat = re.compile(r'<input type="text" name="variableValues\.' + name + r'" size="12" class="page-template-field" disabled=""/> <span class="templateparameter">\(' + name + r'\)</span>')
    n = len(pat.findall(body))
    assert n == 1, "%s: %d" % (name, n)
    body = pat.sub(value, body, count=1)

def replace_img(name, value):
    global body
    pat = re.compile(r'<span class="confluence-embedded-file-wrapper"><img [^>]*template-variable\?name=' + name + r'[^>]*/?>\s*</span>')
    n = len(pat.findall(body))
    assert n == 1, "%s: %d" % (name, n)
    body = pat.sub(value, body, count=1)

# Section 1: History
replace_input("rfc_id", esc(rvs["id"]))
replace_input("req_created_at", esc(rvs["created_at"]))
replace_input("req_requested_for", esc(rvs["requested_for"]))
AUTH_CELL = '<td class="confluenceTd"><div class="content-wrapper"><p><br/></p></div></td></tr></tbody>'
body = body.replace(AUTH_CELL, '<td class="confluenceTd"><div class="content-wrapper"><p>%s</p></div></td></tr></tbody>' % PROFILE_AT, 1)

# Section 3: Общие сведения
replace_input("req_subject", esc(rvs["subject"]))
replace_img("req_uri", AUTH_LINK)  # req_uri — img placeholder, не input!
replace_input("req_id", esc(rvs["id"]))
replace_img("req_template_account", esc(tpl_account))
# Author — @-mention. Заменяем пустую ячейку (изначально могла быть confluence_token_owner, сейчас её нет)
# Ищем пустую ячейку после "Автор"
AUTH_EMPTY = '<strong style="text-align: left;" title="">Автор</strong></td><td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p><br/></p></div></td>'
AUTH_FULL = '<strong style="text-align: left;" title="">Автор</strong></td><td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p>%s</p></div></td>' % PROFILE_AT
n = body.count(AUTH_EMPTY)
if n == 1:
    body = body.replace(AUTH_EMPTY, AUTH_FULL, 1)
    print("Author empty cell replaced")
elif n > 1:
    print("WARNING: %d author empty cells, replacing first" % n)
    body = body.replace(AUTH_EMPTY, AUTH_FULL, 1)
else:
    print("WARNING: author empty cell not found, trying alternate pattern")
    # Пробуем другой вариант — "Автор требования" в разделе 1 (история)
    # И уже обработано выше в разделе 1

# Section 6.1
replace_input("req_first_comment", esc(rvs["first_comment"]))

# Section 8.1
OLD_81 = '<h2 id="DIT4ME-Шаблонзапроса(req_template_subj)"><span class="numhead-number">8.1. </span>Шаблон запроса <input type="text" name="variableValues.req_template_subj" size="12" class="page-template-field" disabled=""/> <span class="templateparameter">(req_template_subj)</span></h2>'
body = body.replace(OLD_81, '<h2 id="DIT4ME-Шаблонзапроса"><span class="numhead-number">8.1. </span>Шаблон запроса %s</h2>' % esc(tpl_subj), 1)

def fill_param_row(label, value, wrapper):
    global body
    if wrapper == "p":
        old = '<tr><td class="confluenceTd"><p>%s</p></td><td class="confluenceTd"><div class="content-wrapper"><p><br/></p></div></td></tr>' % label
        new = '<tr><td class="confluenceTd"><p>%s</p></td><td class="confluenceTd"><div class="content-wrapper"><p>%s</p></div></td></tr>' % (label, value)
    else:
        old = '<tr><td class="confluenceTd"><p>%s</p></td><td class="confluenceTd"><br/></td></tr>' % label
        new = '<tr><td class="confluenceTd"><p>%s</p></td><td class="confluenceTd">%s</td></tr>' % (label, value)
    body = body.replace(old, new, 1)

fill_param_row("Название шаблона", esc(tpl_subj), "p")
fill_param_row("Категория", esc("rfc"), "br")

ui_ext_id = "14567"
ui_ext_name = "Предоставление демо стенда"
fill_param_row("Расширение UI", '%s: %s (вкладка "Информация", %s)' % (ui_ext_id, esc(ui_ext_name),
    '<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/ui_extensions/%s" /><ac:plain-text-body>UI-расширение %s</ac:plain-text-body></ac:link>' % (ui_ext_id, ui_ext_id)), "br")
fill_param_row("Правила автоматизации", "10 правил: 3 на шаблоне (8.1.2), 7 на задачах РП 15785 (8.2.1+)", "br")
fill_param_row("Шаблон рабочего процесса", '15785: %s (<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/workflow_templates/15785" /><ac:plain-text-body>РП 15785</ac:plain-text-body></ac:link>)' % esc(tpl_subj), "br")

# 8.1.1: UI description from file
ui_md = open(os.path.join(UI_DESC, "desc_14567.md"), encoding="utf-8").read()
ui_html = ''
for line in ui_md.split('\n'):
    s = line.strip()
    if not s: continue
    if s.startswith('#'):
        ui_html += '<h5>%s</h5>' % esc(s.lstrip('# ').strip())
    elif s.startswith('|---'):
        continue
    elif s.startswith('|'):
        cells = [c.strip() for c in s.split('|') if c.strip()]
        ui_html += '<table><tbody><tr>' + ''.join('<td><p>%s</p></td>' % esc(c) for c in cells) + '</tr></tbody></table>'
    elif s.startswith('- '):
        ui_html += '<li>%s</li>' % esc(s[2:])
    elif s.startswith('```'):
        continue
    else:
        ui_html += '<p>%s</p>' % esc(s)

OLD_811 = '<h3 id="DIT4ME-ТребованиякРасширениюUI"><span class="numhead-number">8.1.1. </span>Требования к Расширению UI</h3><p><input type="text" name="variableValues.req_ui_ext_ai_desc" size="12" class="page-template-field" disabled=""/> <span class="templateparameter">(req_ui_ext_ai_desc)</span></p>'
body = body.replace(OLD_811, '<h3 id="DIT4ME-ТребованиякРасширениюUI"><span class="numhead-number">8.1.1. </span>Требования к Расширению UI</h3>' + ui_html, 1)

# 8.1.2: Template rules TABLE + full descriptions (rule structure)
tpl_rows = ['<div class="table-wrap"><table class="wrapped confluenceTable" style="width: 100%;">\n<colgroup><col style="width: 5%%;"/><col style="width: 15%%;"/><col style="width: 20%%;"/><col style="width: 15%%;"/><col style="width: 30%%;"/><col style="width: 15%%;"/></colgroup>\n<tbody>\n']
tpl_rows.append('<tr><th><p><strong>\u00ae</strong></p></th><th><p><strong>ID</strong></p></th><th><p><strong>Название</strong></p></th><th><p><strong>Триггер</strong></p></th><th><p><strong>Суть</strong></p></th><th><p><strong>Ссылка</strong></p></th></tr>')
for i, r in enumerate(template_rules, 1):
    tpl_rows.append('<tr><td><p>%d</p></td><td><p>%s</p></td><td><p>%s</p></td><td><p>%s</p></td><td><p>%s</p></td><td><p>%s</p></td></tr>' % (i, esc(r["id"]), esc(r["name"]), esc(r["trigger"]), esc(r["condition"][:120]), card_link(r["id"])))
tpl_rows.append('</tbody></table></div>')
tpl_table = '\n'.join(tpl_rows)

# Build full descriptions for each template rule
for r in template_rules:
    tpl_table += '\n<h4 id="DIT4ME-Подробноеописаниеправило%s">%s</h4>' % (r["id"], esc(r["name"]))
    tpl_table += '\n<p><strong>Настройки правила</strong></p>'
    tpl_table += '\n' + settings_table(r)
    tpl_table += '\n<h4>Выражения</h4>\n' + expressions_table(r)
    tpl_table += '\n<h4>Действия</h4>\n' + actions_table(r)

OLD_812 = '<h3 id="DIT4ME-Требованиякправиламавтоматизации"><span class="numhead-number">8.1.2. </span><span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3><p><input type="text" name="variableValues.req_template_automation_rule_ai_description" size="12" class="page-template-field" disabled=""/> <span class="templateparameter">(req_template_automation_rule_ai_description)</span></p>'
body = body.replace(OLD_812, '<h3 id="DIT4ME-Требованиякправиламавтоматизации"><span class="numhead-number">8.1.2. </span><span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3><p>На шаблоне запроса настроено 3 правила автоматизации:</p>\n' + tpl_table, 1)

# 8.2: Рабочий процесс
OLD_821 = '<h3 id="DIT4ME-ТребованиякРасширениюUI.1"><span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3><p><input type="text" name="variableValues.wf_ui_ext_desc" size="12" class="page-template-field" disabled=""/> <span class="templateparameter">(wf_ui_ext_desc)</span></p>'
body = body.replace(OLD_821, '<h3 id="DIT4ME-ТребованиякРасширениюUI.1"><span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3><p>Отсутствует (у РП 15785 нет своего UI-расширения).</p>', 1)

OLD_822 = '<h3 id="DIT4ME-Требованиякправиламавтоматизации.1"><span class="numhead-number">8.2.2. </span><span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3><p><input type="text" name="variableValues.wf_ar_desc" size="12" class="page-template-field" disabled=""/> <span class="templateparameter">(wf_ar_desc)</span></p>'
body = body.replace(OLD_822, '<h3 id="DIT4ME-Требованиякправиламавтоматизации.1"><span class="numhead-number">8.2.2. </span><span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3><p>Отсутствуют (у РП 15785 нет правил автоматизации).</p>', 1)

# 8.3: 4 subsections with full rule descriptions
def rule_block(rid, rname, trig, essence):
    return ('<h3 id="DIT4ME-Требованиякправилуавтоматизации-%s">Требования к правилу автоматизации %s - %s</h3>'
            '<p>Триггер: %s. Карточка: %s</p>'
            '<p><strong>Настройки правила</strong></p>%s'
            '<h4>Выражения</h4>%s'
            '<h4>Действия</h4>%s'
            % (rid, rid, esc(rname), esc(trig), card_link(rid),
               settings_table(next(r for r in rules_data if r["id"] == rid)),
               expressions_table(next(r for r in rules_data if r["id"] == rid)),
               actions_table(next(r for r in rules_data if r["id"] == rid))))

# Get task rule data
tasks_full = []
for task in TASKS:
    task_rules_data = []
    for rid in task["rule_ids"]:
        task_rules_data.append(next(r for r in rules_data if r["id"] == rid))
    tasks_full.append({"id": task["id"], "name": task["name"], "rules": task_rules_data})

blocks = []
for tid, tname in [("4313", TASKS[0]["name"]), ("7411", TASKS[1]["name"]),
                    ("31693", TASKS[2]["name"]), ("31697", TASKS[3]["name"])]:
    blocks.append('<h2 id="DIT4ME-Шаблонзадачи-%s">Шаблон задачи %s (ID %s)</h2>' % (tid, esc(tname.replace('"', "&quot;")), tid))
    blocks.append('<p>Требования к Расширению UI: Отсутствует (у задачи нет расширения UI).</p>')
    for tr in tasks_full:
        if tr["id"] == tid:
            for r in tr["rules"]:
                blocks.append(rule_block(r["id"], r["name"], r["trigger"], esc(r["condition"][:80])))

NEW_83 = "\n".join(blocks)

# Replace old 8.3 (from static h2 to end of innerCell)
start = body.find('<h2 id="DIT4ME-Шаблонзадачи(task_template_name)">')
assert start != -1, "8.3 not found"
end = body.find('</div>', start)
assert end != -1
body = body[:start] + NEW_83 + '\n</div>' + body[end + len('</div>'):]

# === Validation ===
leftover = [x for x in ("variableValues.", "templateparameter", "template-variable?name=") if x in body]
assert not leftover, "Leftover: " + str(leftover)
ra = re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;|mdash;|laquo;|raquo;)', body)
assert not ra, "Raw &: %d" % len(ra)
try:
    ET.fromstring('<root xmlns:ac="https://ac" xmlns:ri="https://ri">' + body + '</root>')
    print("XML: OK")
except ET.ParseError as e:
    assert False, "XML: " + str(e)[:100]

# Check empty ac:link
empty = re.findall(r'<ac:link><ri:url ri:value="[^"]*"[^>]*/></ac:link>', body)
print("Empty ac:links: %d" % len(empty))
assert len(empty) == 0, "Empty ac:links: %d" % len(empty)

# Save
with open(os.path.join(CONFL, "temp", "page_body_8170964_v22.html"), "w", encoding="utf-8") as f:
    f.write(body)

# === Publish ===
title = "8170964-%s - Предоставление доступа к демо стенду (v2.2)" % tpl_subj
payload = {
    "type": "page",
    "title": title,
    "space": {"key": "DIT4ME"},
    "body": {"storage": {"value": body, "representation": "storage"}},
    "ancestors": [{"id": "735534111"}],
}
result = conf("POST", "/rest/api/content", payload)
page_id = result["id"]
print("Created: %s" % (confl_base + result["_links"]["webui"]))
print("Title: %s" % title)

# Final verification
final = conf("GET", "/rest/api/content/%s?expand=body.storage" % page_id)
fb = final["body"]["storage"]["value"]
print("\n=== FINAL CHECK ===")
print("RFC link:", ">RFC 8170964</a>" in fb)
print("TOC macro:", "toc-macro" in fb)
print("4 task sections:", sum(1 for t in ["Мониторинг сбоев роботизации", "Балансировщик статусов", "Ожидание ответа сервиса", "Авто-закрытие РП"] if "Шаблон задачи " + t in fb))
print("@mention:", "ac:link-body" in fb and "ri:userkey=" in fb)
print("no profile macro:", "ac:name=" + '"profile"' not in fb)
print("numhead-number:", fb.count("numhead-number"))
print("Settings tables:", fb.count("Триггер"))
print("Expressions tables:", fb.count("Выражения"))
print("Actions tables:", fb.count("Действия"))
print("Empty links:", len(re.findall(r'<ac:link><ri:url ri:value="[^"]*"[^>]*/></ac:link>', fb)))
print("Done! Page ID: %s" % page_id)
