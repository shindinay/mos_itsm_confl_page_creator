#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and publish Confluence page for RFC 56363.
"""
import json
import os
import re
import html as html_mod
import urllib.request
import urllib.error

BASE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj"
CONF = os.path.join(BASE, "mos_itsm_confl_page_creator")
ARTIFACT = os.path.join(BASE, "mos_itsm_get_obj_structure", "artifact")

# Load .env
env = json.load(open(os.path.join(CONF, ".env"), encoding="utf-8-sig"))
confl_base = env["CONFLUENCE_BASE_URL"].rstrip("/")
confl_token = env["CONFLUENCE_API_TOKEN"]
space_key = env["ITPM_SPACE_KEY"]
parent_id = "738464880"

# --- Variable values ---
req_id = "56363"
req_uri = "https://itsm.itsm-qa.mos.ru/requests/56363"
req_subject = "МосИТСМ. Предоставление доступа к демо стенду"
req_requested_for = "Наумова Елена Станиславовна"
req_created_at = "2021-10-25T16:30:27+03:00"
req_first_comment = "2021-10-25T16:30:27+03:00 | Наумова Елена Станиславовна: Тема: Восстановить пароль доступа сотруднику структурного подразделения\nКому: 4me_inbound+eps.its@it.mos.ru"
req_template_subj = "МосИТСМ. Предоставление доступа к демо стенду"
req_template_account = "itsm-qa.mos.ru"
confluence_token_owner = "2c98d8026e1c34cb016e45ea6c064b40"

# Load template
with open(os.path.join(CONF, "page_body.html"), encoding="utf-8") as f:
    html = f.read()

# --- Replace input fields ---
html = re.sub(
    r'<input type="text" name="variableValues\.req_id" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_id\)</span>',
    req_id, html)
html = re.sub(
    r'<input type="text" name="variableValues\.req_subject" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_subject\)</span>',
    req_subject, html)
html = re.sub(
    r'<input type="text" name="variableValues\.req_template_subj" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_template_subj\)</span>',
    req_template_subj, html)
html = re.sub(
    r'<input type="text" name="variableValues\.req_requested_for" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_requested_for\)</span>',
    req_requested_for, html)
html = re.sub(
    r'<span style="color: rgb\(0,0,0\);"> <input type="text" name="variableValues\.req_created_at" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_created_at\)</span></span>',
    req_created_at, html)
html = re.sub(
    r'<input type="text" name="variableValues\.req_first_comment" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_first_comment\)</span>',
    req_first_comment, html)

# --- Replace template-variable images ---
html = html.replace(
    '<span class="confluence-embedded-file-wrapper">'
    '<img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" '
    'src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_uri" '
    'data-image-src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_uri"/>'
    '</span>',
    '<a href="' + req_uri + '">RFC ' + req_id + '</a>')

html = html.replace(
    '<span class="confluence-embedded-file-wrapper">'
    '<img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" '
    'src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_template_account" '
    'data-image-src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_template_account"/>'
    '</span>',
    req_template_account)

html = html.replace(
    '<span style="color: rgb(112,112,112);"><span><em>'
    '<span class="confluence-embedded-file-wrapper">'
    '<img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" '
    'src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=confluence_token_owner" '
    'data-image-src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=confluence_token_owner"/>'
    '</span></em></span></span>',
    '<ac:link><ac:link-body><ri:user ri:userkey="' + confluence_token_owner + '"/></ac:link-body></ac:link>')

# Replace remaining placeholder inputs
remaining_inputs = re.findall(
    r'<input type="text" name="variableValues\.[^"]*"[^>]*/>'
    r' <span class="templateparameter">\([^)]+\)</span>', html)
for inp in remaining_inputs:
    html = html.replace(inp, "(не задано)")

# ============================================================
# RULE DESCRIPTIONS (hardcoded from API responses)
# ============================================================

def ac_rule_link(rid, rname):
    return '<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/automation_rules/' + str(rid) + '" /><ac:plain-text-body>Карточка правила ' + str(rid) + ': ' + html_mod.escape(rname) + '</ac:plain-text-body></ac:link>'

def ac_ui_link(eid, ename):
    return '<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/ui_extensions/' + str(eid) + '" /><ac:plain-text-body>Карточка расширения UI ' + str(eid) + ': ' + html_mod.escape(ename) + '</ac:plain-text-body></ac:link>'

def rule_table(trig, cond):
    return '<table class="relative-table wrapped confluenceTable"><colgroup><col style="width: 30%;"/><col style="width: 70%;"/></colgroup><tbody>' +\
           '<tr><td class="confluenceTd"><strong>Триггер</strong></td><td class="confluenceTd">' + trig + '</td></tr>' +\
           '<tr><td class="confluenceTd"><strong>Условие</strong></td><td class="confluenceTd"><code>' + html_mod.escape(cond) + '</code></td></tr>' +\
           '</tbody></table>'

def expr_table(expressions):
    lines = ['<table class="relative-table wrapped confluenceTable"><colgroup><col style="width: 40%;"/><col style="width: 60%;"/></colgroup><tbody>',
             '<tr><th class="confluenceTh"><p>Имя выражения</p></th><th class="confluenceTh"><p>Логика</p></th></tr>']
    for e in expressions:
        ename = e["name"]
        eexpr = e["expression"]
        if len(eexpr) > 150:
            eexpr = html_mod.escape(eexpr[:150]) + " ..."
        else:
            eexpr = html_mod.escape(eexpr)
        lines.append('<tr><td class="confluenceTd"><p>' + html_mod.escape(ename) + '</p></td>')
        lines.append('<td class="confluenceTd"><p><code>' + eexpr + '</code></p></td></tr>')
    lines.append('</tbody></table>')
    return '\n'.join(lines)

def actions_table(actions):
    lines = ['<table class="relative-table wrapped confluenceTable"><colgroup><col style="width: 40%;"/><col style="width: 60%;"/></colgroup><tbody>',
             '<tr><th class="confluenceTh"><p>Действие</p></th><th class="confluenceTh"><p>Описание</p></th></tr>']
    for k, v in actions.items():
        vstr = str(v)
        if len(vstr) > 200:
            vstr = html_mod.escape(vstr[:200]) + " ..."
        else:
            vstr = html_mod.escape(vstr)
        lines.append('<tr><td class="confluenceTd"><p><code>' + html_mod.escape(k) + '</code></p></td>')
        lines.append('<td class="confluenceTd"><p>' + vstr + '</p></td></tr>')
    lines.append('</tbody></table>')
    return '\n'.join(lines)

def describe_rule_block(rid, rname, trigger, condition, expressions, actions):
    parts = []
    parts.append('<p>' + ac_rule_link(rid, rname) + '</p>')
    parts.append(rule_table(trigger, condition))
    if expressions:
        parts.append(expr_table(expressions))
    if actions:
        parts.append(actions_table(actions))
    return '\n'.join(parts)

# --- Template-level rules (3 rules) ---
template_rules = [
    {
        "id": 10249331, "name": "Закрыть запрос если переоткрыли",
        "trigger": "on status update", "condition": "was_completed and is_not_completed",
        "expressions": [
            {"name": "was_completed", "expression": "status_was = completed"},
            {"name": "is_not_completed", "expression": "status != completed"}
        ],
        "actions": {
            "action1": "set member = member_was",
            "action2": "set status = completed",
            "action3": "set completion_reason = completion_reason_was",
            "action5": "add note 'Выполнение данного запроса полностью автоматизировано: ...'"
        }
    },
    {
        "id": 10249443, "name": "Создать запрос в Р-Сервис. Заказ демо-стенда (ApiGate 1.0)",
        "trigger": "on status update", "condition": "is_wf_pending and !was_wf_pending",
        "expressions": [
            {"name": "is_wf_pending", "expression": "status = workflow_pending"},
            {"name": "was_wf_pending", "expression": "status_was = workflow_pending"},
            {"name": "was_completed", "expression": "status_was = completed"},
            {"name": "SystemSourceObjCode", "expression": "id"},
            {"name": "x4meaccount", "expression": "account.id"},
            {"name": "emails1", "expression": "find_all(person, custom_fields.emails).map(primary_email)"},
            {"name": "emails", "expression": '"{{emails1}}".replace(",",...).replace("[",...)'},
            {"name": "subject", "expression": '"МосИТСМ № {{SystemSourceObjCode}}"'},
            {"name": "template_id", "expression": '"147"'},
            {"name": "ContactPhone", "expression": '"+79891234987"'},
            {"name": "ContactEmail", "expression": "member.primary_email"},
            {"name": "DescriptionShort", "expression": '"Доступ к демо-стенду R-Service {{subject}}"'},
            {"name": "DescriptionFull", "expression": '"Связанный запрос {{subject}}"'},
            {"name": "ContactFIO", "expression": "requested_by.name"}
        ],
        "actions": {
            "action6": "call webhook 'АТ. ApiGate 1.0 Передача в HPSM'"
        }
    },
    {
        "id": 13553013, "name": "Завершить после решения от р-сервис",
        "trigger": "on custom_fields update", "condition": "note_vendor and request_vendor and !is_completed and note_was_updated",
        "expressions": [
            {"name": "note_vendor", "expression": "custom_fields.note_rservice != null"},
            {"name": "request_vendor", "expression": "custom_fields.request_rservice != null"},
            {"name": "robot", "expression": "find(person, 3)"},
            {"name": "jarvis_team", "expression": "find(team, 835)"},
            {"name": "is_completed", "expression": "status = completed"},
            {"name": "request_vendor_text", "expression": "custom_fields.note_rservice"},
            {"name": "note_was_updated", "expression": "custom_fields_was.note_rservice != custom_fields.note_rservice"}
        ],
        "actions": {
            "action1": "set status = completed",
            "action2": "set completion_reason = solved",
            "action3": "add note '{{request_vendor_text}}'",
            "action4": "set team = jarvis_team",
            "action5": "set member = robot",
            "action6": "update workflow set status = completed",
            "action7": "update workflow set completion_reason = complete",
            "action8": "update workflow add note 'Запрос успешно завершен'"
        }
    }
]

# --- Task template rules ---
task_rules_data = [
    # Task 4313: Мониторинг сбоев роботизации
    {
        "tt_id": 4313,
        "tt_subject": 'Мониторинг сбоев роботизации. Команда "ДИТ.MOS.ITSM.Администраторы"',
        "tt_phase": "Исполнение",
        "tt_failure": None,
        "rules": [
            {
                "id": 1914157, "name": "Генерация задачи на обработку",
                "trigger": "on status update", "condition": "is_assigned and failed_present",
                "expressions": [
                    {"name": "is_assigned", "expression": "status = assigned"},
                    {"name": "new_task", "expression": "new(task, \"Обработка сбоев автоматизации (Автогенерация)\")"},
                    {"name": "all_failed_tasks", "expression": "workflow.tasks.select(status = failed)"},
                    {"name": "failed_task", "expression": "all_failed_tasks.select(status = failed)[last]"},
                    {"name": "failed_present", "expression": "all_failed_tasks.size > 0"}
                ],
                "actions": {
                    "action7": "add note 'Для обработки сбоя задачи [{{failed_name}}] была сгенерирована новая задача'",
                    "action8": "update new_task add note 'Произошел сбой в автоматизированной задаче ...'",
                    "action11": "update new_task set phase_name = phase",
                    "action17": "update new_task set subject = fail_subject",
                    "action19": "update workflow add new_task to tasks",
                    "action20": "update new_task add failed_task_successors to successors",
                    "action22": "update new_task set instructions = fail_instruction",
                    "action23": "update all_failed_tasks set status = canceled"
                }
            },
            {
                "id": 1914235, "name": "Возврат статуса зарегистрировано",
                "trigger": "on status update", "condition": "is_assigned and (!no_failed_predecessors or !no_registered_predecessors)",
                "expressions": [
                    {"name": "is_assigned", "expression": "status = assigned"},
                    {"name": "no_registered_predecessors", "expression": "predecessors.select(status = registered).size = 0"},
                    {"name": "no_failed_predecessors", "expression": "predecessors.select(status = failed).size = 0"}
                ],
                "actions": {
                    "action1": "set status = registered"
                }
            },
            {
                "id": 1991869, "name": "Автозавершение",
                "trigger": "on status update", "condition": "no_failed_predecessors and no_registered_predecessors and (is_assigned or is_in_progress)",
                "expressions": [
                    {"name": "is_in_progress", "expression": "status = in_progress"},
                    {"name": "is_assigned", "expression": "status = assigned"},
                    {"name": "no_registered_predecessors", "expression": "predecessors.select(status = registered).size = 0"},
                    {"name": "no_failed_predecessors", "expression": "workflow.tasks.select(status = failed).size = 0"}
                ],
                "actions": {
                    "action1": "set status = completed"
                }
            }
        ]
    },
    # Task 7411: Балансировщик статусов
    {
        "tt_id": 7411,
        "tt_subject": "Балансировщик статусов",
        "tt_phase": "Исполнение",
        "tt_failure": None,
        "rules": [
            {
                "id": 2655131, "name": "Завершить при назначении",
                "trigger": "on status update", "condition": "is_assigned",
                "expressions": [
                    {"name": "is_assigned", "expression": "status = assigned"}
                ],
                "actions": {
                    "action1": "set status = completed"
                }
            }
        ]
    },
    # Task 31693: Ожидание ответа сервиса
    {
        "tt_id": 31693,
        "tt_subject": "Ожидание ответа сервиса. Предоставление доступа к демо стенду",
        "tt_phase": "Исполнение",
        "tt_failure": {"id": 4313, "name": "Мониторинг сбоев роботизации. Команда \"ДИТ.MOS.ITSM.Администраторы\""},
        "rules": [
            {
                "id": 13934317, "name": "Запуск таймера сбоя",
                "trigger": "on status update", "condition": "is_assigned and is_robotic",
                "expressions": [
                    {"name": "is_assigned", "expression": "status = assigned"},
                    {"name": "is_robotic", "expression": "member.id = 3"},
                    {"name": "delay", "expression": "find(calendar,\"Рабочие дни 9-18 для Согласования\").target_at(now,24.hours)"}
                ],
                "actions": {
                    "action1": "after delay_debug trigger 'Сбой обработки'"
                }
            },
            {
                "id": 13934321, "name": "Сбой обработки",
                "trigger": "after delay", "condition": "is_assigned and is_robotic",
                "expressions": [
                    {"name": "is_assigned", "expression": "status = assigned"},
                    {"name": "is_robotic", "expression": "member.id = 3"},
                    {"name": "parent_req_id", "expression": "workflow.requests[first].id"},
                    {"name": "vendor_link_open", "expression": '"https://mos.r-service.tech/requests?vstate=completed&q={{parent_req_id}}"'}
                ],
                "actions": {
                    "action1": "set status = failed",
                    "action3": "add note 'Запрос №{{parent_req_id}} не был обработан автоматически в течение SLA вендора. ...'"
                }
            }
        ]
    },
    # Task 31697: Авто-закрытие РП
    {
        "tt_id": 31697,
        "tt_subject": "Авто-закрытие РП. Предоставление доступа к демо стенду",
        "tt_phase": "Исполнение",
        "tt_failure": None,
        "rules": [
            {
                "id": 13935097, "name": "Проброс коммента в запрос, закрытие РП и запроса",
                "trigger": "on status update", "condition": "is_assigned",
                "expressions": [
                    {"name": "is_assigned", "expression": "status = assigned"},
                    {"name": "req", "expression": "workflow.requests[first]"},
                    {"name": "robot", "expression": "find(person, 3)"},
                    {"name": "jarvis_team", "expression": "find(team, 835)"}
                ],
                "actions": {
                    "action4": "update req add note 'При обработке запроса возникли ошибки, но их причина на текущий момент исправлена. ...'",
                    "action5": "update req set status = completed",
                    "action6": "update req set completion_reason = solved",
                    "action1": "update workflow add note 'Автоматическое завершение РП'",
                    "action2": "update workflow set status = completed",
                    "action3": "update workflow set completion_reason = complete",
                    "action7": "update req set team = jarvis_team",
                    "action8": "update req set member = robot"
                }
            }
        ]
    }
]

# --- UI Extension description for template ---
ui_ext_id = 14567
ui_ext_name = "Предоставление демо стенда"
ui_ext_title = "Информация"
ui_ext_desc = '<p>' + ac_ui_link(ui_ext_id, ui_ext_name) + '</p>' +\
              '<table class="relative-table wrapped confluenceTable"><colgroup><col style="width: 30%;"/><col style="width: 70%;"/></colgroup><tbody>' +\
              '<tr><th class="confluenceTh"><p>Заголовок вкладки</p></th><td class="confluenceTd"><p>Информация</p></td></tr>' +\
              '<tr><th class="confluenceTh"><p>Подсказки</p></th><td class="confluenceTd"><p>/custom_views/1897/suggest</p></td></tr>' +\
              '<tr><th class="confluenceTh"><p>Макс. количество</p></th><td class="confluenceTd"><p>100 лиц</p></td></tr>' +\
              '</tbody></table>'

# --- Build 8.1.2: Template automation rules ---
t812 = ''
for i, r in enumerate(template_rules, 1):
    t812 += '<h4 id="DIT4ME-Требованиякправиламавтоматизации.' + str(i) + '"><span class="numhead-number">8.1.2.' + str(i) + '. </span>Требования к правилу автоматизации ' + str(i) + ' - ' + html_mod.escape(r["name"]) + '</h4>'
    t812 += describe_rule_block(r["id"], r["name"], r["trigger"], r["condition"], r["expressions"], r["actions"])
    t812 += '<p><br/></p>'

# --- Build 8.2: Task templates ---
t82 = ''
num = 1
for tt in task_rules_data:
    tt_id = tt["tt_id"]
    tt_subj = tt["tt_subject"]
    t82 += '<h3 id="DIT4ME-Шаблонзадачи' + str(tt_id) + '"><span class="numhead-number">8.2.' + str(num) + '. </span>Шаблон задачи ' + html_mod.escape(tt_subj) + '</h3>'
    # No UI for tasks
    t82 += '<h4 id="DIT4ME-ТребованиякРасширениюUI.' + str(tt_id) + '"><span class="numhead-number">8.2.' + str(num) + '.1. </span>Требования к Расширению UI</h4>'
    t82 += '<p>Отсутствует</p>'
    # Rules
    for j, r in enumerate(tt["rules"], 1):
        t82 += '<h4 id="DIT4ME-Требованиякправиламм' + str(r["id"]) + '"><span class="numhead-number">8.2.' + str(num) + '.' + str(j) + '. </span>Требования к правилу автоматизации ' + str(j) + ' - ' + html_mod.escape(r["name"]) + '</h4>'
        t82 += describe_rule_block(r["id"], r["name"], r["trigger"], r["condition"], r["expressions"], r["actions"])
        t82 += '<p><br/></p>'
    # Failure task
    if tt["tt_failure"]:
        t82 += '<p><strong>Задача при сбое:</strong> ' + html_mod.escape(tt["tt_failure"]["name"]) + ' (ID: ' + str(tt["tt_failure"]["id"]) + ')</p>'
    num += 1

# --- Replace section 8.1.1 ---
html = re.sub(
    r'<h3 id="DIT4ME-ТребованиякРасширениюUI"[^>]*>.*?</h3>\s*<p>.*?</p>',
    '<h3 id="DIT4ME-ТребованиякРасширениюUI"><span class="numhead-number">8.1.1. </span>Требования к Расширению UI</h3>' + ui_ext_desc,
    html, flags=re.DOTALL)

# --- Replace section 8.1.2 ---
html = re.sub(
    r'<h3 id="DIT4ME-Требованиякправиламавтоматизации"[^>]*>.*?</h3>\s*<h2',
    '<h3 id="DIT4ME-Требованиякправиламавтоматизации"><span class="numhead-number">8.1.2. </span>Требования к правилам автоматизации</h3>' + t812 + '<h2',
    html, flags=re.DOTALL)

# --- Replace section 8.2 (workflow rules + tasks) ---
html = re.sub(
    r'<h3 id="DIT4ME-ТребованиякРасширениюUI\.1"[^>]*>.*?</h3>\s*<p>.*?</p>\s*'
    r'<h3 id="DIT4ME-Требованиякправиламавтоматизации\.1"[^>]*>.*?</h3>\s*<p>.*?</p>',
    '<h3 id="DIT4ME-ТребованиякРасширениюUI.1"><span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3>' +
    '<p>Расширения UI у задач рабочего процесса отсутствуют.</p>' +
    '<h3 id="DIT4ME-Требованиякправиламавтоматизации.1"><span class="numhead-number">8.2.2. </span>Требования к правилам автоматизации</h3>' + t82,
    html, flags=re.DOTALL)

# --- Remove old 8.3 placeholder ---
html = re.sub(
    r'<h2 id="DIT4ME-Шаблонзадачи[^"]*"[^>]*>.*?</h2>',
    '', html, flags=re.DOTALL)

# --- Fix TOC: replace old 8.2/8.3 with task entries ---
old_toc = re.search(
    r"<li><a href='#TemplatePreview-ШаблонРабочегопроцесса'>8\.2\. Шаблон Рабочего процесса</a>\s*"
    r"<ul class='toc-indentation'>.*?</ul>\s*</li>\s*"
    r"<li><a href='#TemplatePreview-Требованиякправиламавтоматизации\.2'>8\.3\.2.*?</li>",
    html, flags=re.DOTALL)
if old_toc:
    new_toc = "<li><a href='#TemplatePreview-ШаблонРабочегопроцесса'>8.2. Шаблон Рабочего процесса</a><ul class='toc-indentation'>"
    for i, tt in enumerate(task_rules_data, 1):
        new_toc += "<li><a href='#DIT4ME-Шаблонзадачи" + str(tt['tt_id']) + "'>" + str(i) + ".2. " + tt['tt_subject'] + "</a></li>"
    new_toc += "</ul></li>"
    html = html.replace(old_toc.group(0), new_toc)

# --- Save filled page body ---
out_path = os.path.join(CONF, "page_body_56363_filled_v2.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Saved filled page body to:", out_path)
print("File size:", os.path.getsize(out_path), "bytes")

# Verify
remaining = re.findall(r'template-variable\?name=([^"\']+)', html)
if remaining:
    print("WARNING: Remaining placeholders:", remaining)
else:
    print("All placeholders replaced successfully.")

# ============================================================
# PUBLISH TO CONFLUENCE
# ============================================================

title = "56363-МосИТСМ. Предоставление доступа к демо стенду - Предоставление доступа к демо стенду"

# Create page
payload = {
    "type": "page",
    "title": title,
    "space": {"key": space_key},
    "body": {"storage": {"value": html, "representation": "storage"}},
    "ancestors": [{"id": parent_id}],
    "properties": {
        "template": {"id": env["ITPM_TEMPLATE_ID"]}
    }
}

# Save payload
payload_path = os.path.join(CONF, "payload_56363_v2.json")
with open(payload_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

# POST
req = urllib.request.Request(
    confl_base + "/rest/api/content",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": "Bearer " + confl_token,
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    page_id = result["id"]
    page_url = result["_links"]["base"] + result["_links"]["webui"]
    print("\nPage created successfully!")
    print("ID:", page_id)
    print("URL:", page_url)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print("\nError creating page:", e.code)
    print(body)
