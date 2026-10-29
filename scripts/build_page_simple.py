#!/usr/bin/env python3
"""Simple placeholder replacement in original template - no structural changes."""

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

# Load template - NO MODIFICATIONS to structure
with open("C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_confl_page_creator/template_body.html", "r", encoding="utf-8") as f:
    body = f.read()

# === Helper: replace input+span placeholder with value ===
def replace_placeholder(body, variable_name, replacement):
    pattern = r'<input[^>]*name="variableValues\.' + re2.escape(variable_name) + r'"[^>]*/?>\s*<span class="templateparameter">\(' + re2.escape(variable_name) + '\)</span>'
    if re2.search(pattern, body):
        return re2.sub(pattern, replacement, body, count=1)
    return body

# === Section 1: History ===
# rfc_id
body = replace_placeholder(body, 'rfc_id', '<span class="numhead-number">' + esc(req_id) + '</span>')
# req_created_at - wrapped in existing <span style="color: rgb(0,0,0);">
body = replace_placeholder(body, 'req_created_at', esc(req_created_at))
# req_requested_for
body = replace_placeholder(body, 'req_requested_for', esc(req_requested_for))
# Author - replace empty <p></p> with ac_user
# The Author column has: <div class="content-wrapper"><p></p></div>
# Replace the first occurrence in the history table row
author_pattern = r'(<td class="confluenceTd"><div class="content-wrapper"><p>)\s*</p>\s*(</div></td></tr>)'
body = re2.sub(author_pattern, r'\1' + ac_user(userkey) + r'\2', body, count=1)

# === Section 3: General info ===
# req_subject
body = replace_placeholder(body, 'req_subject', esc(req_subject))

# req_uri - replace img placeholder with <a href>
# Original: <span class="confluence-embedded-file-wrapper"><img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_uri" data-image-src="..."></span>
uri_img_pattern = r'<span class="confluence-embedded-file-wrapper"><img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" src="https://itpm-wiki\.mos\.ru/plugins/servlet/confluence/placeholder/template-variable\?name=req_uri"[^>]*/?>\s*</span>'
uri_replacement = '<a href="' + esc(req_uri) + '">RFC ' + esc(req_id) + '</a> <span class="templateparameter">(req_uri)</span>'
body = re2.sub(uri_img_pattern, uri_replacement, body, count=1)

# req_id
body = replace_placeholder(body, 'req_id', esc(req_id))

# req_template_account - leave as is (img placeholder for account info)

# Author in general info - second empty <p></p> in Author column
author2_pattern = r'(Автор</strong></td><td style="text-align: left;" class="confluenceTd"><div class="content-wrapper)<p>\s*</p>\s*(</div></td>)'
body = re2.sub(author2_pattern, r'\1<p>' + ac_user(userkey) + r'\2', body, count=1)

# === Section 6: Business requirements ===
# req_first_comment
body = replace_placeholder(body, 'req_first_comment', esc(req_first_comment))

# === Section 8.1: Request template ===
# req_template_subj
body = replace_placeholder(body, 'req_template_subj', esc(template_subject))

# req_ui_ext_ai_desc (8.1.1)
ui_desc = 'Расширение UI ' + str(ui_ext_rt["id"]) + ' ' + esc(ui_ext_rt["name"]) + ' (активная версия ' + str(ui_ext_full["active_version"]["id"]) + ') предназначено для сбора списка лиц, которым предоставляется доступ к демо-стенду при регистрации запроса по шаблону. Вкладка "Информация" содержит одно заполняемое поле "Список лиц" (мультивыбор из представления "лица_без_локальных", до 100 записей, обязательное). Остальные поля - служебные скрытые (data-internal, data-hidden).'
body = replace_placeholder(body, 'req_ui_ext_ai_desc', ui_desc)

# === Section 8.1.2: Automation rules for request template ===
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
body = re2.sub(ar_pattern, rule812_content, body, count=1)

# === Section 8.1 table: Fill template info ===
# Replace empty cells in the template table
# Название шаблона
body = re2.sub(r'(<tr><td class="confluenceTd"><p>Название шаблона</p></td><td class="confluenceTd"><div class="content-wrapper"><p>)\s*(</p></div></td></tr>)',
               r'\1' + esc(template_subject) + r'\2', body, count=1)

# Категория
body = re2.sub(r'(<tr><td class="confluenceTd"><p>Категория</p></td><td class="confluenceTd)">\s*(</td></tr>)',
               r'\1<p>' + esc(category) + r'\2', body, count=1)

# Расширение UI
body = re2.sub(r'(<tr><td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd)">\s*(</td></tr>)',
               r'\1<p>' + ac_link("https://itsm.itsm-qa.mos.ru/ui_extensions/14567", "Карточка расширения UI 14567") + r'\2', body, count=1)

# Правила автоматизации
rule_links = []
for ar in ar_template:
    rule_links.append(ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + str(ar["id"]), "Правило " + str(ar["id"])))

rules_table_cell = '<tr><td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd"><p>'
for i, rl in enumerate(rule_links):
    if i > 0:
        rules_table_cell += '<br/>'
    rules_table_cell += rl
rules_table_cell += '</p></td></tr>'

body = re2.sub(r'(<tr><td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd)">\s*(</td></tr>)',
               r'\1' + rules_table_cell[66:] + r'\2', body, count=1)

# Шаблон рабочего процесса
body = re2.sub(r'(<tr><td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd)">\s*(</td></tr>)',
               r'\1<p>' + ac_link("https://itsm.itsm-qa.mos.ru/workflow_templates/" + str(wf_id), "Карточка РП " + str(wf_id)) + r'\2', body, count=1)

# === Section 8.2: Workflow ===
# wf_ui_ext_desc
body = replace_placeholder(body, 'wf_ui_ext_desc', 'Расширение UI не задано (отсутствует).')

# wf_ar_desc
body = replace_placeholder(body, 'wf_ar_desc', ac_link("https://itsm.itsm-qa.mos.ru/workflow_templates/" + str(wf_id), "Карточка РП " + str(wf_id)))

# === Section 8.3: Task templates - replace static placeholder ===
wf = structure["workflow_template"]
task_templates = wf["task_templates"]

def parse_rule_desc_v2(ar):
    ar_id = str(ar["id"])
    ar_name = ar["name"]
    ar_trigger = ar["trigger"]
    desc_file = "C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_automation_rule_descriptor/artifact/desc_" + ar_id + ".md"
    try:
        with open(desc_file, "r", encoding="utf-8") as f:
            desc_content = f.read()
    except FileNotFoundError:
        return ar_id, ar_name, ar_trigger, [], [], ''

    cond_text = ''
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

    task_sections += '<h2 id="TaskTemplate' + str(tt_id) + '"><span class="numhead-number">8.' + str(section_num) + '. </span>Шаблон задачи "' + safe_tt_subject + '"</h2>'
    task_sections += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/task_templates/" + str(tt_id), "Карточка шаблона задачи " + str(tt_id)) + '</p>'

    phase_info = 'Фаза: ' + esc(tt_phase) + '. Категория: ' + esc(tt_category)
    if tt_team:
        phase_info += '. Ответственная команда: ' + esc(tt_team)
    task_sections += '<p>' + phase_info + '</p>'

    task_sections += '<h3 id="ReqUIExt' + str(tt_id) + '"><span class="numhead-number">8.' + str(section_num) + '.1. </span>Требования к Расширению UI</h3>'
    if tt.get("ui_extension"):
        task_sections += '<p>' + ac_link("https://itsm.itsm-qa.mos.ru/ui_extensions/" + str(tt["ui_extension"]["id"]), "Карточка расширения UI " + str(tt["ui_extension"]["id"])) + '</p>'
    else:
        task_sections += '<p>Расширение UI не задано (отсутствует).</p>'

    task_sections += '<h3 id="ReqAutoRule' + str(tt_id) + '"><span class="numhead-number">8.' + str(section_num) + '.2. </span><span>Требования к правилам автоматизации</span></h3>'

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

# Replace static 8.3 placeholder with actual task template sections
# Find the h2 with task_template_name and everything up to the next columnLayout or end of content
static_83_pattern = r'<h2 id="DIT4ME-Шаблонзадачи\(task_template_name\)">.*?</h2>.*?(?=<div class="columnLayout|$)'
if re2.search(static_83_pattern, body, re2.DOTALL):
    body = re2.sub(static_83_pattern, task_sections, body, count=1, flags=re2.DOTALL)
else:
    print("WARNING: static 8.3 placeholder not found")

# Write output
with open("C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_confl_page_creator/page_body_8170964_final.html", "w", encoding="utf-8") as f:
    f.write(body)

print("Page body written: " + str(len(body)) + " bytes")

# Count ac:link blocks
ac_links = re2.findall(r'<ac:link>(.*?)</ac:link>', body, re2.DOTALL)
print("ac:link blocks: " + str(len(ac_links)))
