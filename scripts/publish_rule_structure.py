# -*- coding: utf-8 -*-
"""Загружает правила через API, добавляет секции Настройки/Выражения/Действия
в таблицу 8.1.2 и в подразделы задач, затем обновляет страницу."""
import json, re, os, sys
import xml.etree.ElementTree as ET
import ssl, urllib.request, urllib.error

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFL = SKILL
AR_DESC = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\artifact"
UI_DESC = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_UI-extension_creator\artifact"

env = json.load(open(os.path.join(CONFL, ".env"), encoding="utf-8-sig"))
itsm_token = env["MOSITSM_PERS_TOKEN_QA"]
confl_base = env["CONFLUENCE_BASE_URL"].rstrip("/")
confl_token = env["CONFLUENCE_API_TOKEN"]

ctx = ssl._create_unverified_context()

def confl_req(method, path, data=None):
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

def itsm_get(endpoint, token=itsm_token, account="itsm"):
    url = "https://api.itsm-qa.mos.ru/v1/" + endpoint
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token,
              "X-4me-Account": account, "Accept": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def card_link(rid, text=None):
    t = text or "Карточка правила " + rid
    return '<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/automation_rules/%s" /><ac:plain-text-body>%s</ac:plain-text-body></ac:link>' % (rid, esc(t))

# === Load all rules ===
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
    rules_data.append({
        "id": rid, "name": rname,
        "trigger": r.get("trigger", ""),
        "condition": cond,
        "expressions": expressions,
        "actions": actions,
    })
    print("Rule %s: %d expr, %d actions" % (rid, len(expressions), len(actions)))

# Group
template_rules = rules_data[:3]  # template
task_rules = rules_data[3:]      # task-level

TASKS = [
    {"id": "4313", "name": "Мониторинг сбоев роботизации. Команда \"ДИТ.MOS.ITSM.Администраторы\"",
     "rule_ids": ["1914157", "1914235", "1991869"]},
    {"id": "7411", "name": "Балансировщик статусов",
     "rule_ids": ["2655131"]},
    {"id": "31693", "name": "Ожидание ответа сервиса. Предоставление доступа к демо стенду",
     "rule_ids": ["13934317", "13934321"]},
    {"id": "31697", "name": "Авто-закрытие РП. Предоставление доступа к демо стенду",
     "rule_ids": ["13935097"]},
]

def build_settings_table(rule):
    rows = []
    rows.append("<table><tbody>")
    rows.append("<tr><td><p><strong>Триггер</strong></p></td><td><p>%s</p></td></tr>" % esc(rule["trigger"]))
    rows.append("<tr><td><p><strong>Условие</strong></p></td><td><p>%s</p></td></tr>" % esc(rule["condition"]))
    rows.append("</tbody></table>")
    return "\n".join(rows)

def build_expressions_table(rule):
    rows = ["<table><tbody>"]
    rows.append("<tr><th><p><strong>Имя выражения</strong></p></th><th><p><strong>Логика</strong></p></th></tr>")
    for name, value in rule["expressions"]:
        rows.append("<tr><td><p>%s</p></td><td><p>%s</p></td></tr>" % (esc(name), esc(value)))
    rows.append("</tbody></table>")
    return "\n".join(rows)

def build_actions_table(rule):
    rows = ["<table><tbody>"]
    rows.append("<tr><th><p><strong>Действие</strong></p></th><th><p><strong>Описание</strong></p></th></tr>")
    for atype, avalue in rule["actions"]:
        rows.append("<tr><td><p>%s</p></td><td><p>%s</p></td></tr>" % (esc(atype), esc(avalue)))
    rows.append("</tbody></table>")
    return "\n".join(rows)

# === Load page ===
page_id = "738464817"
page = confl_req("GET", "/rest/api/content/%s?expand=body.storage" % page_id)
body = page["body"]["storage"]["value"]
print("Loaded page, len=%d" % len(body))

# === Section 8.1.2: replace with full structure ===
h3_pos = body.find("id=\"DIT4ME-Требованиякправиламавтоматизации\">")
assert h3_pos != -1, "8.1.2 not found"
h2_82_pos = body.find("id=\"DIT4ME-ШаблонРабочегоПроцесса\">")
assert h2_82_pos != -1, "8.2 not found"

# Build new 8.1.2
new_block = '<h3 id="DIT4ME-Требованиякправиламавтоматизации">Требования к правилам автоматизации</h3>\n'
new_block += '<p>На шаблоне запроса настроено 3 правила автоматизации:</p>\n'
new_block += '<div class="table-wrap"><table class="wrapped confluenceTable" style="width: 100%;">\n'
new_block += '<colgroup><col style="width: 5%%;"/><col style="width: 15%%;"/><col style="width: 20%%;"/><col style="width: 15%%;"/><col style="width: 30%%;"/><col style="width: 15%%;"/></colgroup>\n'
new_block += '<tbody>\n'
new_block += '<tr><th><p><strong>\u00ae</strong></p></th><th><p><strong>ID</strong></p></th>'
new_block += '<th><p><strong>Название</strong></p></th><th><p><strong>Триггер</strong></p></th>'
new_block += '<th><p><strong>Суть</strong></p></th><th><p><strong>Ссылка</strong></p></th></tr>\n'

for i, rule in enumerate(template_rules, 1):
    new_block += '<tr>'
    new_block += '<td><p>%d</p></td>' % i
    new_block += '<td><p>%s</p></td>' % esc(rule["id"])
    new_block += '<td><p>%s</p></td>' % esc(rule["name"])
    new_block += '<td><p>%s</p></td>' % esc(rule["trigger"])
    new_block += '<td><p>%s</p></td>' % esc(rule["condition"][:150])
    new_block += '<td><p>%s</p></td>' % card_link(rule["id"])
    new_block += '</tr>\n'

new_block += '</tbody></table></div>\n'

# Full descriptions below
for rule in template_rules:
    new_block += '<h4 id="DIT4ME-Подробноеописаниеправила%s">%s</h4>\n' % (rule["id"], esc(rule["name"]))
    new_block += build_settings_table(rule) + '\n'
    new_block += '<h4>Выражения</h4>\n'
    new_block += build_expressions_table(rule) + '\n'
    new_block += '<h4>Действия</h4>\n'
    new_block += build_actions_table(rule) + '\n'

body = body[:h3_pos] + new_block + body[h2_82_pos:]
print("8.1.2 updated with full rule structure")

# === Task subsections: add full rule descriptions ===
for task in TASKS:
    for rid in task["rule_ids"]:
        rule = next(r for r in rules_data if r["id"] == rid)
        h3_search = "Требования к правилу автоматизации %s - " % rid
        h3_pos = body.find(h3_search)
        if h3_pos == -1:
            print("  WARNING: h3 not found for rule %s" % rid)
            continue
        h3_end = body.find("</h3>", h3_pos) + len("</h3>")
        
        full_desc = '<p><strong>Описание:</strong> '
        full_desc += build_settings_table(rule)
        full_desc += '\n<h5>Выражения</h5>\n'
        full_desc += build_expressions_table(rule)
        full_desc += '\n<h5>Действия</h5>\n'
        full_desc += build_actions_table(rule)
        
        body = body[:h3_end] + full_desc + body[h3_end:]

print("Task subsections updated with full rule structure")

# === Validation ===
leftover = [x for x in ("variableValues.", "templateparameter", "template-variable?name=") if x in body]
print("Leftover placeholders:", leftover)
empty = re.findall(r'<ac:link><ri:url ri:value="[^"]*"[^>]*/></ac:link>', body)
print("Empty ac:links:", len(empty))
ra = re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;|mdash;|laquo;|raquo;)', body)
print("Raw &: %d" % len(ra))
try:
    ET.fromstring('<root xmlns:ac="https://ac" xmlns:ri="https://ri">' + body + '</root>')
    print("XML: OK")
except ET.ParseError as e:
    print("XML: FAIL - " + str(e)[:100])

# Save
out_path = os.path.join(SKILL, "temp", "page_body_8170964_v22_fixed.html")
open(out_path, "w", encoding="utf-8").write(body)

# Publish v2
payload = {
    "id": page_id,
    "version": {"number": page["version"]["number"] + 1},
    "body": {"storage": {"value": body, "representation": "storage"}},
}
result = confl_req("PUT", "/rest/api/content/%s" % page_id, payload)
print("\nPublished v%d" % page["version"]["number"] + 1)
print("URL: %s/pages/viewpage.action?pageId=%s" % (confl_base, page_id))

# Final check
final = confl_req("GET", "/rest/api/content/%s?expand=body.storage" % page_id)
fb = final["body"]["storage"]["value"]
print("\n=== FINAL CHECK ===")
print("Settings tables:", fb.count("Триггер"))
print("Expressions tables:", fb.count("Выражения"))
print("Actions tables:", fb.count("Действия"))
print("Empty links:", len(re.findall(r'<ac:link><ri:url ri:value="[^"]*"[^>]*/></ac:link>', fb)))
print("numhead-number:", fb.count("numhead-number"))
print("done")
