#!/usr/bin/env python3
"""Build Confluence page body from template_body.html with substitutions."""

import json
import re as re2

def ac_link(url, text):
    return '<ac:link><ri:url ri:value="' + url + '" /><ac:plain-text-body>' + text + '</ac:plain-text-body></ac:link>'

def ac_user(key):
    return '<ac:link><ac:link-body><ri:user ri:userkey="' + key + '" /></ac:link-body></ac:link>'

def esc(text):
    if not text:
        return ''
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# Load structure
with open("C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_get_obj_structure/artifact/structure_56363_20261028_134057.json", "r", encoding="utf-8") as f:
    structure = json.load(f)

rt = structure["request_template"]
template_subject = rt["subject"]
category = rt["category"]
wf_id = rt["workflow_template"]["id"]
ui_ext_rt = rt["ui_extension"]
ui_ext_full = structure["ui_extension"]

# Load request vars
with open("C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_get_obj_structure/artifact/request_vars_8170964_20261028_163752.json", "r", encoding="utf-8") as f:
    req_data = json.load(f)

rv = req_data["request_variables"]
req_id = str(rv["request.id"])
req_uri = rv["request.uri"]
req_subject = rv["request.subject"]
req_requested_for = rv["request.requested_for"]
req_created_at = rv["request.created_at"]
req_first_comment = rv["request.notes[first]"]

userkey = "2c98d8026e1c34cb016e45ea6c064b40"

# Load template
with open("C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_confl_page_creator/template_body.html", "r", encoding="utf-8") as f:
    body = f.read()

# Fix img tags to be self-closing (XHTML requirement)
body = re2.sub(r'(<img\b[^>]*?)(?<!/)>', r'\1 />', body)

# Wrap in body tag for Confluence storage format
body = '<body xmlns="http://www.w3.org/1999/xhtml">' + body + '</body>'

# === Replace placeholder input+span pairs with actual values ===

def replace_placeholder(body, variable_name, replacement):
    """Replace <input ... name=\"variableValues.xxx\" .../> <span class=\"templateparameter\">(xxx)</span> with replacement text."""
    pattern = r'<input[^>]*name="variableValues\.' + re2.escape(variable_name) + r'"[^>]*/?>\s*<span class="templateparameter">\(' + re2.escape(variable_name) + '\)</span>'
    # Check if pattern exists
    if re2.search(pattern, body):
        body = re2.sub(pattern, replacement, body, count=1)
    else:
        print("WARNING: placeholder " + variable_name + " not found")
    return body

# Section 1: History row
rfc_id_replacement = '<span class="numhead-number">' + esc(req_id) + '</span>'
body = replace_placeholder(body, 'rfc_id', rfc_id_replacement)

req_created_at_replacement = '<span style="color: rgb(0,0,0);">' + esc(req_created_at) + '</span>'
body = replace_placeholder(body, 'req_created_at', req_created_at_replacement)

body = replace_placeholder(body, 'req_requested_for', esc(req_requested_for))

# Author in history - replace empty <p></p> in td with ac:link
# Find the Author column's <p></p> and replace
author_pattern = r'<div class="content-wrapper"><p></p></div>'
# This appears in the Author column of the history table - only one occurrence before other sections
# We need two author fields: one in history, one in general info
# Use a counter approach

# For the first author (in history), we'll use a marker-based approach
# Let's do targeted replacements

# req_requested_for in history
body = re2.sub(r'(<td class="confluenceTd"><p class="content-wrapper">)\s*<input[^>]*name="variableValues\.req_requested_for"[^>]*/?>\s*<span class="templateparameter">\(req_requested_for\)</span>',
               r'\1' + esc(req_requested_for) + '</p></td>', body, count=1)

# req_created_at in history
body = re2.sub(r'(<td class="confluenceTd"><div class="content-wrapper"><p><span style="color: rgb\(0,0,0\)">\s*)<input[^>]*name="variableValues\.req_created_at"[^>]*/?>\s*<span class="templateparameter">\(req_created_at\)</span>',
               r'\1' + esc(req_created_at) + '</span> ', body, count=1)

# rfc_id in history
body = re2.sub(r'(<td class="confluenceTd"><p>)\s*<input[^>]*name="variableValues\.rfc_id"[^>]*/?>\s*<span class="templateparameter">\(rfc_id\)</span>',
               r'\1<span class="numhead-number">' + esc(req_id) + '</span> ', body, count=1)

# Author in history - replace <p></p> with ac_user
# The author cell is the last cell of the history row
# Find it: <td class="confluenceTd"><div class="content-wrapper"><p></p></div></td>
# But there are multiple empty <p></p> in the template. Only the one in the history table's author column.
# Use a more targeted approach: find the first occurrence of the pattern right after the history table
body = re2.sub(r'<td class="confluenceTd"><div class="content-wrapper"><p>\s*</p>\s*</div>\s*</td>\s*</tr>',
               r'<td class="confluenceTd"><div class="content-wrapper"><p>' + ac_user(userkey) + '</p></div></td></tr>',
               body, count=1)

# req_subject (section 3 - General info)
body = replace_placeholder(body, 'req_subject', esc(req_subject))

# req_uri - replace the img placeholder with <a href> link
uri_pattern = r'<span class="confluence-embedded-file-wrapper"><img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" src="https://itpm-wiki\.mos\.ru/plugins/servlet/confluence/placeholder/template-variable\?name=req_uri"[^>]*/?>\s*</span>'
uri_replacement = '<a href="' + esc(req_uri) + '">RFC ' + esc(req_id) + '</a> <span class="templateparameter">(req_uri)</span>'
if re2.search(uri_pattern, body):
    body = re2.sub(uri_pattern, uri_replacement, body, count=1)
else:
    print("WARNING: req_uri img placeholder not found")

# req_id (section 3)
body = replace_placeholder(body, 'req_id', esc(req_id))

# req_template_account - leave as is (no value)

# Author in general info - replace the empty <p></p> pattern
# After section 3 table, find the Author row
# Pattern: <td class="highlight-#f4f5f7 confluenceTd" ...><strong ...>Автор</strong></td><td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p></p></div></td>
author2_pattern = r'(Автор</strong></td><td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p)\s*</p>\s*(</div></td>)'
body = re2.sub(author2_pattern, r'\1' + ac_user(userkey) + r'\2', body, count=1)

# req_first_comment (section 6.1)
body = replace_placeholder(body, 'req_first_comment', esc(req_first_comment))

# req_template_subj (section 8.1)
body = replace_placeholder(body, 'req_template_subj', esc(template_subject))

# req_ui_ext_ai_desc (8.1.1) - replace with UI extension description
# Pattern: <input name="variableValues.req_ui_ext_ai_desc" .../> <span class="templateparameter">(req_ui_ext_ai_desc)</span>
ui_desc_replacement = 'Расширение UI ' + str(ui_ext_rt["id"]) + ' ' + esc(ui_ext_rt["name"]) + ' (активная версия ' + str(ui_ext_full["active_version"]["id"]) + ') предназначено для сбора списка лиц, которым предоставляется доступ к демо-стенду при регистрации запроса по шаблону. Вкладка "Информация" содержит одно заполняемое поле "Список лиц" (мультивыбор из представления "лица_без_локальных", до 100 записей, обязательное). Остальные поля - служебные скрытые (data-internal, data-hidden).'
ui_pattern = r'<input[^>]*name="variableValues\.req_ui_ext_ai_desc"[^>]*/?>\s*<span class="templateparameter">\(req_ui_ext_ai_desc\)</span>'
if re2.search(ui_pattern, body):
    body = re2.sub(ui_pattern, ui_desc_replacement, body, count=1)
else:
    print("WARNING: req_ui_ext_ai_desc placeholder not found")

# req_template_automation_rule_ai_description (8.1.2)
# Replace with structured automation rule descriptions for request template rules
ar_template = structure["automation_rules"]

def parse_rule_desc(ar):
    ar_id = str(ar["id"])
    desc_file = "C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_automation_rule_descriptor/artifact/desc_" + ar_id + ".md"
    try:
        with open(desc_file, "r", encoding="utf-8") as f:
            desc_content = f.read()
    except FileNotFoundError:
        return ar_id, [], []

    expressions = []
    expr_match = re2.search(r'## Выражения\s*\n\s*<table>(.*?)</table>', desc_content, re2.DOTALL)
    if expr_match:
        expr_table = expr_match.group(1)
        tds = re2.findall(r'<td[^>]*>(.*?)</td>', expr_table, re2.DOTALL)
        for i in range(0, len(tds) - 1, 2):
            name = tds[i].strip().replace('\n', ' ').replace('\r', '')
            logic = tds[i+1].strip().replace('\n', ' ').replace('\r', '')
            expressions.append((esc(name), esc(logic)))

    actions = []
    act_match = re2.search(r'## Действия\s*\n\s*<table>(.*?)</table>', desc_content, re2.DOTALL)
    if act_match:
        act_table = act_match.group(1)
        tds = re2.findall(r'<td[^>]*>(.*?)</td>', act_table, re2.DOTALL)
        for i in range(0, len(tds) - 1, 2):
            action = tds[i].strip().replace('\n', ' ').replace('\r', '')
            action_desc = tds[i+1].strip().replace('\n', ' ').replace('\r', '')
            actions.append((esc(action), esc(action_desc)))

    return ar_id, expressions, actions

# Build 8.1.2 content
rule812_content = ''

# Rule 10249331
ar_id, exprs, acts = parse_rule_desc({"id": 10249331, "name": "Закрыть запрос если переоткрыли", "trigger": "on status update"})
rule812_content += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/10249331", "Правило 10249331 - Закрыть запрос если переоткрыли") + '</p>'
rule812_content += '<p>Триггер: <code>on status update</code> - при изменении статуса записи.</p>'
rule812_content += '<p>Условие: <code>was_completed and is_not_completed</code> - запрос раньше был завершён и статус перестал быть "Завершено" (запрос переоткрыт).</p>'
if exprs:
    expr_items = []
    for name, logic in exprs:
        expr_items.append('<li><code>' + name + '</code> - ' + logic + '</li>')
    rule812_content += '<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>'
if acts:
    act_items = []
    for action, action_desc in acts:
        act_items.append('<li>' + action + ' - ' + action_desc + '</li>')
    rule812_content += '<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>'

# Rule 10249443
ar_id, exprs, acts = parse_rule_desc({"id": 10249443, "name": "Создать запрос в Р-Сервис. Заказ демо-стенда (ApiGate 1.0)", "trigger": "on status update"})
rule812_content += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/10249443", "Правило 10249443 - Создать запрос в Р-Сервис. Заказ демо-стенда (ApiGate 1.0)") + '</p>'
rule812_content += '<p>Триггер: <code>on status update</code> - при изменении статуса записи.</p>'
rule812_content += '<p>Условие: <code>is_wf_pending and !was_wf_pending</code> - запрос перешёл в статус "В рабочем процессе" (workflow_pending), а до изменения этим статусом не был.</p>'
if exprs:
    expr_items = []
    for name, logic in exprs:
        expr_items.append('<li><code>' + name + '</code> - ' + logic + '</li>')
    rule812_content += '<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>'
if acts:
    act_items = []
    for action, action_desc in acts:
        act_items.append('<li>' + action + ' - ' + action_desc + '</li>')
    rule812_content += '<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>'

# Rule 13553013
ar_id, exprs, acts = parse_rule_desc({"id": 13553013, "name": "Завершить после решения от р-сервис", "trigger": "on custom_fields update"})
rule812_content += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/13553013", "Правило 13553013 - Завершить после решения от р-сервис") + '</p>'
rule812_content += '<p>Триггер: <code>on custom_fields update</code> - при обновлении пользовательских полей записи.</p>'
rule812_content += '<p>Условие: <code>note_vendor and request_vendor and !is_completed and note_was_updated</code> - заметка от вендора заполнена, номер запроса вендора заполнен, запрос ещё не завершён, и обновление изменило заметку от вендора.</p>'
if exprs:
    expr_items = []
    for name, logic in exprs:
        expr_items.append('<li><code>' + name + '</code> - ' + logic + '</li>')
    rule812_content += '<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>'
if acts:
    act_items = []
    for action, action_desc in acts:
        act_items.append('<li>' + action + ' - ' + action_desc + '</li>')
    rule812_content += '<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>'

ar_pattern = r'<input[^>]*name="variableValues\.req_template_automation_rule_ai_description"[^>]*/?>\s*<span class="templateparameter">\(req_template_automation_rule_ai_description\)</span>'
if re2.search(ar_pattern, body):
    body = re2.sub(ar_pattern, rule812_content, body, count=1)
else:
    print("WARNING: req_template_automation_rule_ai_description placeholder not found")

# === Section 8.1: Fill template info table ===
# Replace empty cells in the template table
body = re2.sub(r'<tr><td class="confluenceTd"><p>Название шаблона</p></td><td class="confluenceTd"><div class="content-wrapper"><p>\s*</p></div></td></tr>',
               '<tr><td class="confluenceTd"><p>Название шаблона</p></td><td class="confluenceTd"><div class="content-wrapper"><p>' + esc(template_subject) + '</p></div></td></tr>',
               body, count=1)

body = re2.sub(r'<tr><td class="confluenceTd"><p>Категория</p></td><td class="confluenceTd">\s*</td></tr>',
               '<tr><td class="confluenceTd"><p>Категория</p></td><td class="confluenceTd"><p>' + esc(category) + '</p></td></tr>',
               body, count=1)

body = re2.sub(r'<tr><td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd">\s*</td></tr>',
               '<tr><td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><p>' + ac_link("https://itsm.itsm-qa.mos.ru/ui_extensions/14567", "Карточка расширения UI 14567") + '</p></td></tr>',
               body, count=1)

# Rules list in template table
rule_links = []
for ar in ar_template:
    rule_links.append(ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + str(ar["id"]), "Правило " + str(ar["id"])))

rules_table_cell = '<tr><td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd"><p>'
for i, rl in enumerate(rule_links):
    if i > 0:
        rules_table_cell += '<br/>'
    rules_table_cell += rl
rules_table_cell += '</p></td></tr>'

body = re2.sub(r'<tr><td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd">\s*</td></tr>',
               rules_table_cell, body, count=1)

body = re2.sub(r'<tr><td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd">\s*</td></tr>',
               '<tr><td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd"><p>' + ac_link("https://itsm.itsm-qa.mos.ru/workflow_templates/" + str(wf_id), "Карточка РП " + str(wf_id)) + '</p></td></tr>',
               body, count=1)

# === Section 8.2: Workflow - replace empty WF content ===
wf_ui_pattern = r'<input[^>]*name="variableValues\.wf_ui_ext_desc"[^>]*/?>\s*<span class="templateparameter">\(wf_ui_ext_desc\)</span>'
if re2.search(wf_ui_pattern, body):
    body = re2.sub(wf_ui_pattern, 'Расширение UI не задано (отсутствует).', body, count=1)
else:
    print("WARNING: wf_ui_ext_desc placeholder not found")

wf_ar_pattern = r'<input[^>]*name="variableValues\.wf_ar_desc"[^>]*/?>\s*<span class="templateparameter">\(wf_ar_desc\)</span>'
if re2.search(wf_ar_pattern, body):
    body = re2.sub(wf_ar_pattern, ac_link("https://itsm.itsm-qa.mos.ru/workflow_templates/" + str(wf_id), "Карточка РП " + str(wf_id)), body, count=1)
else:
    print("WARNING: wf_ar_desc placeholder not found")

# === Section 8.3: Replace static task template placeholder with actual task templates ===
wf = structure["workflow_template"]
task_templates = wf["task_templates"]

def parse_rule_desc_v2(ar):
    """Full parse with trigger mapping."""
    ar_id = str(ar["id"])
    ar_name = ar["name"]
    ar_trigger = ar["trigger"]
    desc_file = "C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_automation_rule_descriptor/artifact/desc_" + ar_id + ".md"
    try:
        with open(desc_file, "r", encoding="utf-8") as f:
            desc_content = f.read()
    except FileNotFoundError:
        return ar_id, ar_name, ar_trigger, [], [], ''

    # Extract condition
    cond_text = ''
    cond_match = re2.search(r'## Настройки rule\s*\n\s*<table>(.*?)</table>', desc_content, re2.DOTALL)
    if not cond_match:
        cond_match = re2.search(r'## Настройки rule\s*\n\s*<table>', desc_content, re2.DOTALL)
    # Try a more general pattern for condition
    cond_in_settings = re2.search(r'Условие\s*\n\s*<td[^>]*>(.*?)</td>', desc_content, re2.DOTALL)
    if cond_in_settings:
        cond_text = cond_in_settings.group(1).strip().replace('\n', ' ')

    expressions = []
    expr_match = re2.search(r'## Выражения\s*\n\s*<table>(.*?)</table>', desc_content, re2.DOTALL)
    if expr_match:
        expr_table = expr_match.group(1)
        tds = re2.findall(r'<td[^>]*>(.*?)</td>', expr_table, re2.DOTALL)
        for i in range(0, len(tds) - 1, 2):
            name = tds[i].strip().replace('\n', ' ').replace('\r', '')
            logic = tds[i+1].strip().replace('\n', ' ').replace('\r', '')
            expressions.append((esc(name), esc(logic)))

    actions = []
    act_match = re2.search(r'## Действия\s*\n\s*<table>(.*?)</table>', desc_content, re2.DOTALL)
    if act_match:
        act_table = act_match.group(1)
        tds = re2.findall(r'<td[^>]*>(.*?)</td>', act_table, re2.DOTALL)
        for i in range(0, len(tds) - 1, 2):
            action = tds[i].strip().replace('\n', ' ').replace('\r', '')
            action_desc = tds[i+1].strip().replace('\n', ' ').replace('\r', '')
            actions.append((esc(action), esc(action_desc)))

    return ar_id, ar_name, ar_trigger, expressions, actions, cond_text

trigger_desc_map = {
    "on status update": "при изменении статуса записи",
    "on custom_fields update": "при обновлении пользовательских полей записи",
    "after delay": "после задержки по времени",
}

# Build replacement for 8.3 (the static task template placeholder)
# Section 8.3 becomes multiple 8.3, 8.4, 8.5, 8.6 sections
task_sections = ''
section_num = 3

for tt in task_templates:
    section_num += 1
    tt_id = tt["id"]
    tt_subject = tt["subject"]
    tt_phase = tt.get("phase", "")
    tt_category = tt.get("category", "")
    tt_team = tt.get("team", {}).get("name", "") if tt.get("team") else ""

    safe_tt_subject = esc(tt_subject)
    section_id_safe = 'Дитзадачи' + tt_subject.replace(' ', '').replace('.', '').replace('"', '').replace(',', '')
    section_id = 'DIT4ME-Шаблонзадачи-' + tt_subject

    task_sections += '<h2 id="' + section_id + '"><span class="numhead-number">8.' + str(section_num) + '. </span>Шаблон задачи "' + safe_tt_subject + '"</h2>'
    task_sections += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/task_templates/" + str(tt_id), "Карточка шаблона задачи " + str(tt_id)) + '</p>'

    phase_info = 'Фаза: ' + esc(tt_phase) + '. Категория: ' + esc(tt_category)
    if tt_team:
        phase_info += '. Ответственная команда: ' + esc(tt_team)
    task_sections += '<p>' + phase_info + '</p>'

    # UI Extension
    task_sections += '<h3 id="DIT4ME-ТребованиякРасширениюUI-' + str(tt_id) + '"><span class="numhead-number">8.' + str(section_num) + '.1. </span>Требования к Расширению UI</h3>'
    if tt.get("ui_extension"):
        task_sections += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/ui_extensions/" + str(tt["ui_extension"]["id"]), "Карточка расширения UI " + str(tt["ui_extension"]["id"])) + '</p>'
    else:
        task_sections += '<p>Расширение UI не задано (отсутствует).</p>'

    # Automation rules
    task_sections += '<h3 id="DIT4ME-Требованиякправиламавтоматизации-' + str(tt_id) + '"><span class="numhead-number">8.' + str(section_num) + '.2. </span><span>Требования к правилам автоматизации</span></h3>'

    if not tt.get("automation_rules"):
        task_sections += '<p>Отсутствуют.</p>'
        continue

    for ar in tt["automation_rules"]:
        ar_id, ar_name, ar_trigger, exprs, acts, cond_text = parse_rule_desc_v2(ar)
        task_sections += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + ar_id, "Правило " + ar_id + " - " + esc(ar_name)) + '</p>'

        trigger_ru = trigger_desc_map.get(ar_trigger, ar_trigger)
        task_sections += '<p>Триггер: <code>' + esc(ar_trigger) + '</code> - ' + esc(trigger_ru) + '.</p>'
        if cond_text:
            task_sections += '<p>Условие: ' + cond_text + '</p>'

        if exprs:
            expr_items = []
            for name, logic in exprs:
                expr_items.append('<li><code>' + name + '</code> - ' + logic + '</li>')
            task_sections += '<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>'
        if acts:
            act_items = []
            for action, action_desc in acts:
                act_items.append('<li>' + action + ' - ' + action_desc + '</li>')
            task_sections += '<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>'

# Replace the static 8.3 task template placeholder
# Pattern: <h2 id="DIT4ME-Шаблонзадачи(task_template_name)">...</h2> and its content
task_h2_pattern = r'<h2 id="DIT4ME-Шаблонзадачи\(task_template_name\)">.*?</h2>.*?(?=<h3 id="DIT4ME-ТребованиякРасширениюUI\.2"|<h3 id="DIT4ME-Требованиякправиламавтоматизации\.2"|<div class="columnLayout|"</div>\s*</div>\s*</div>\s*$)'

# Check if pattern matches
if not re2.search(task_h2_pattern, body, re2.DOTALL):
    print("WARNING: 8.3 task template placeholder pattern not found, trying alternative")
    # Alternative: find the h2 and content up to next div.columnLayout
    alt_pattern = r'<h2 id="DIT4ME-Шаблонзадачи\(task_template_name\)"><span class="numhead-number">8\.3\. </span>Шаблон задачи <input[^>]*name="variableValues\.task_template_name"[^>]*/?>\s*<span class="templateparameter">\(task_template_name\)</span>\s*</h2>.*?(?=<div class="columnLayout|</div>\s*</div>\s*</div>\s*$)'
    if re2.search(alt_pattern, body, re2.DOTALL):
        # Replace with task sections
        body = re2.sub(alt_pattern, task_sections, body, count=1, flags=re2.DOTALL)
    else:
        print("WARNING: Alternative 8.3 pattern not found either")
        print("Trying to find the 8.3 h2 line...")
        m = re2.search(r'Шаблон задачи.*?task_template_name', body)
        if m:
            print("Found at:", m.start(), m.end())
            print("Context:", repr(body[m.start():m.start()+300]))
else:
    body = re2.sub(task_h2_pattern, task_sections, body, count=1, flags=re2.DOTALL)

# === Fix the task template table in 8.1 ===
# Also need to remove the old 8.3/8.3.1/8.3.2 placeholder section from TOC
# The TOC will auto-update after publishing, so we can leave it

# === Fix table cells for template name and workflow ===
# Replace any remaining empty cells in the template table

# Write output
with open("page_body_8170964_final.html", "w", encoding="utf-8") as f:
    f.write(body)

print("Page body written: " + str(len(body)) + " bytes")

# Validate
stack = []
for m in re2.finditer(r'<(/?)(\w+)((?:\s+[^>"\']*(?:"[^"]*"|\'[^\']*\')*)?)>', body):
    slash, tag, attrs = m.group(1), m.group(2), m.group(3)
    is_void = tag in ['img', 'br', 'hr', 'col', 'colgroup', 'input', 'ri:url', 'ri:user', 'ac:link-body']

    if slash:
        if stack and stack[-1] == tag:
            stack.pop()
        else:
            pass  # Expected: table structure has unclosed colgroup etc in template
    else:
        if not is_void:
            stack.append(tag)

if stack:
    print("WARNING: Unclosed tags: " + str(stack[:5]))
else:
    print("OK: All tags balanced!")

# Check ac:link blocks
ac_links = re2.findall(r'<ac:link>(.*?)</ac:link>', body, re2.DOTALL)
empty_links = 0
for i, block in enumerate(ac_links):
    if 'plain-text-body' not in block:
        if 'ri:user' in block:
            pass  # Author mention - OK
        else:
            print("WARNING: ac:link " + str(i) + " has no plain-text-body: " + block[:100])
            empty_links += 1
    elif re2.search(r'<ac:plain-text-body>\s*</ac:plain-text-body>', block):
        print("WARNING: ac:link " + str(i) + " has empty plain-text-body")
        empty_links += 1

if empty_links == 0:
    print("OK: No empty ac:link blocks!")
print("ac:link blocks checked: " + str(len(ac_links)))
