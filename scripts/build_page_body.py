#!/usr/bin/env python3
"""Build valid XHTML page body for Confluence from structure JSON."""

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
template_id = rt["id"]
template_subject = rt["subject"]
category = rt["category"]
wf_id = rt["workflow_template"]["id"]
ui_ext_rt = rt["ui_extension"]  # UI ext for request template (no active_version)

# Top-level ui_extension has active_version
ui_ext_full = structure["ui_extension"]  # has active_version

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

L = []  # lines

def w(s):
    L.append(s)

# Start body with Confluence namespace
w('<ac:rich-text-body xmlns:ac="http://www.atlassian.com/schema/confluence/liveconnect" xmlns:ri="http://www.atlassian.com/schema/confluence/sd/com.atlassian.confluence.storage.ConfluenceStorageFormat">')

# ===== Section 1: History =====
w('<div class="contentLayout2">')
w('<div class="columnLayout single" data-layout="single">')
w('<div class="cell normal" data-type="normal">')
w('<div class="innerCell">')
w('<h1 id="DIT4ME-Историяизменений"><span class="numhead-number">1. </span>История изменений</h1>')
w('<div class="table-wrap"><table class="relative-table wrapped confluenceTable" style="width: 47.424%;"><colgroup class=""><col class="" style="width: 16.6063%;"/><col class="" style="width: 13.1941%;"/><col class="" style="width: 19.2224%;"/><col class="" style="width: 50.9317%;"/></colgroup><tbody class="">')
w('<tr class=""><th class="confluenceTh"><p><span style="color: rgb(0,0,0);">Запрос в MOS.ITSM</span></p></th>')
w('<th class="confluenceTh"><p><span style="color: rgb(0,0,0);">Дата создания</span></p></th>')
w('<th class="confluenceTh"><p><span style="color: rgb(0,0,0);">Инициатор</span></p></th>')
w('<th class="confluenceTh"><p><span style="color: rgb(0,0,0);">Автор требования</span></p></th></tr>')
w('<tr class=""><td class="confluenceTd"><p><span class="numhead-number">' + esc(req_id) + '</span> <span class="templateparameter">(rfc_id)</span></p></td>')
w('<td class="confluenceTd"><div class="content-wrapper"><p><span style="color: rgb(0,0,0);">' + esc(req_created_at) + '</span> <span class="templateparameter">(req_created_at)</span></p></div></td>')
w('<td class="confluenceTd"><p class="content-wrapper">' + esc(req_requested_for) + '</p></td>')
w('<td class="confluenceTd"><div class="content-wrapper"><p>' + ac_user(userkey) + '</p></div></td></tr>')
w('</tbody></table></div>')
w('<h1 class="enh-settings hidden hidden" id="DIT4ME-{&quot;enableNumbering&quot;:true}"><span class="numhead-number">2. </span>{&quot;enableNumbering&quot;:true}</h1>')
w('</div></div></div>')

# ===== Section 3: General info =====
w('<div class="columnLayout single" data-layout="single">')
w('<div class="cell normal" data-type="normal">')
w('<div class="innerCell">')
w('<h1 id="DIT4ME-Общиесведения"><span class="numhead-number">3. </span>Общие сведения</h1>')
w('<div class="plugin-tabmeta-details"><div class="table-wrap"><table class="relative-table wrapped confluenceTable" style="width: 60.103%;"><colgroup class=""><col class="" style="width: 25.8165%;"/><col class="" style="width: 74.1538%;"/></colgroup><tbody>')
w('<tr><td class="highlight-#f4f5f7 confluenceTd" style="text-align: left;" title="Цвет фона: Светло-серый 100 %" data-highlight-colour="#f4f5f7"><strong title="">Описание запрошенного требования</strong></td>')
w('<td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p>' + esc(req_subject) + '</p></div></td></tr>')
w('<tr><td class="highlight-#f4f5f7 confluenceTd" style="text-align: left;" title="Цвет фона: Светло-серый 100 %" data-highlight-colour="#f4f5f7"><strong style="text-align: left;" title="">Ссылка на запрос</strong></td>')
w('<td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p><a href="' + esc(req_uri) + '">RFC ' + esc(req_id) + '</a> <span class="templateparameter">(req_uri)</span></p></div></td></tr>')
w('<tr><td class="highlight-#f4f5f7 confluenceTd" style="text-align: left;" title="Цвет фона: Светло-серый 100 %" data-highlight-colour="#f4f5f7"><strong style="text-align: left;" title="">Запрос</strong></td>')
w('<td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p>' + esc(req_id) + '</p></div></td></tr>')
w('<tr class=""><td class="highlight-#f4f5f7 confluenceTd" style="text-align: left;" title="Цвет фона: Светло-серый 100 %" data-highlight-colour="#f4f5f7"><strong style="text-align: left;" title="">Пространство поставщика услуги</strong></td>')
w('<td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><span class="confluence-embedded-file-wrapper"><img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_template_account" data-image-src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_template_account" /></span></div></td></tr>')
w('<tr class=""><td class="highlight-#f4f5f7 confluenceTd" style="text-align: left;" title="Цвет фона: Светло-серый 100 %" data-highlight-colour="#f4f5f7"><strong style="text-align: left;" title="">Автор</strong></td>')
w('<td style="text-align: left;" class="confluenceTd"><div class="content-wrapper"><p>' + ac_user(userkey) + '</p></div></td></tr>')
w('<tr class=""><td class="highlight-#f4f5f7 confluenceTd" style="text-align: left;" title="Цвет фона: Светло-серый 100 %" data-highlight-colour="#f4f5f7"><strong style="text-align: left;" title="">Согласующий от Поставщика</strong></td>')
w('<td class="confluenceTd">&lt;пока указать вручную&gt;</td></tr>')
w('</tbody></table></div></div></div>')
w('</div></div></div>')

# ===== Section 4: TOC =====
w('<div class="columnLayout single" data-layout="single">')
w('<div class="cell normal" data-type="normal">')
w('<div class="innerCell">')
w('<h1 id="DIT4ME-Оглавление"><span class="numhead-number">4. </span>Оглавление</h1>')
w('<p><style type=\'text/css\'>')
w('div.rbtoc1793195172884 {padding: 0px;}')
w('div.rbtoc1793195172884 ul {margin-left: 0px;}')
w('div.rbtoc1793195172884 li {margin-left: 0px;padding-left: 0px;}')
w('</style><div class=\'toc-macro rbtoc1793195172884\'>')
w('<ul class=\'toc-indentation\'>')
w('<li><a href=\'#TemplatePreview-Историяизменений\'>1. История изменений</a></li>')
w('<li><a href=\'#TemplatePreview-{&quot;enableNumbering&quot;:true}\'>2. {&quot;enableNumbering&quot;:true}</a></li>')
w('<li><a href=\'#TemplatePreview-Общиесведения\'>3. Общие сведения</a></li>')
w('<li><a href=\'#TemplatePreview-Оглавление\'>4. Оглавление</a></li>')
w('<li><a href=\'#TemplatePreview-Связанныетребования(пометкам)\'>5. Связанные требования (по меткам)</a></li>')
w('<li><a href=\'#TemplatePreview-Бизнес-требования\'>6. Бизнес-требования</a>')
w('<ul class=\'toc-indentation\'>')
w('<li><a href=\'#TemplatePreview-Изначальнаяпостановка\'>6.1. Изначальная постановка</a></li>')
w('<li><a href=\'#TemplatePreview-ОписаниеПроблемы\'>6.2. Описание Проблемы</a></li>')
w('<li><a href=\'#TemplatePreview-РешениеПроблемы\'>6.3. Решение Проблемы</a></li>')
w('</ul></li>')
w('<li><a href=\'#TemplatePreview-Описаниеавтоматизируемогобизнеспроцесса\'>7. Описание автоматизируемого бизнес процесса</a></li>')
w('<li><a href=\'#TemplatePreview-Требованиякобъектамсистемы\'>8. Требования к объектам системы</a>')
w('<ul class=\'toc-indentation\'>')
w('<li><a href=\'#TemplatePreview-Шаблонзапроса\'>8.1. Шаблон запроса</a>')
w('<ul class=\'toc-indentation\'>')
w('<li><a href=\'#TemplatePreview-ТребованиякРасширениюUI\'>8.1.1. Требования к Расширению UI</a></li>')
w('<li><a href=\'#TemplatePreview-Требованиякправиламавтоматизации\'>8.1.2. Требования к правилам автоматизации</a></li>')
w('</ul></li>')
w('<li><a href=\'#TemplatePreview-ШаблонРабочегопроцесса\'>8.2. Шаблон Рабочего процесса</a>')
w('<ul class=\'toc-indentation\'>')
w('<li><a href=\'#TemplatePreview-ТребованиякРасширениюUI.1\'>8.2.1. Требования к Расширению UI</a></li>')
w('<li><a href=\'#TemplatePreview-Требованиякправиламавтоматизации.1\'>8.2.2. Требования к правилам автоматизации</a></li>')
w('</ul></li>')
w('<li><a href=\'#TemplatePreview-Шаблонзадачи\'>8.3. Шаблон задачи</a>')
w('<ul class=\'toc-indentation\'>')
w('<li><a href=\'#TemplatePreview-ТребованиякРасширениюUI.2\'>8.3.1. Требования к Расширению UI</a></li>')
w('<li><a href=\'#TemplatePreview-Требованиякправиламавтоматизации.2\'>8.3.2. Требования к правилам автоматизации</a></li>')
w('</ul></li>')
w('</ul></li></ul></div></p></div>')
w('</div></div></div>')

# ===== Section 5: Related =====
w('<div class="columnLayout single" data-layout="single">')
w('<div class="cell normal" data-type="normal">')
w('<div class="innerCell">')
w('<h1 id="DIT4ME-Связанныетребования(пометкам)"><span class="numhead-number">5. </span>Связанные требования (по меткам)</h1><p><br/></p></div></div></div>')

# ===== Section 6: Business requirements =====
w('<div class="columnLayout single" data-layout="single">')
w('<div class="cell normal" data-type="normal">')
w('<div class="innerCell">')
w('<h1 id="DIT4ME-Бизнес-требования"><span class="numhead-number">6. </span><span>Бизнес-требования</span></h1>')
w('<h2 id="DIT4ME-Изначальнаяпостановка"><span class="numhead-number">6.1. </span>Изначальная постановка</h2>')
safe_note = esc(req_first_comment)
w('<p>' + safe_note + '</p>')
w('<h2 class="auto-cursor-target" id="DIT4ME-ОписаниеПроблемы"><span class="numhead-number">6.2. </span>Описание Проблемы</h2><p><br/></p>')
w('<h2 class="auto-cursor-target" id="DIT4ME-РешениеПроблемы"><span class="numhead-number">6.3. </span>Решение Проблемы</h2><p><br/></p>')
w('</div></div></div>')

# ===== Section 7: Business process =====
w('<div class="columnLayout single" data-layout="single">')
w('<div class="cell normal" data-type="normal">')
w('<div class="innerCell">')
w('<h1 id="DIT4ME-Описаниеавтоматизируемогобизнеспроцесса"><span class="numhead-number">7. </span>Описание автоматизируемого бизнес процесса</h1><p><em><span style="color: rgb(0,0,255);">&lt;(заглушка) текст для заполнения вручную&gt;</span></em></p></div></div></div>')

# ===== Section 8: Requirements to system objects =====
w('<div class="columnLayout single" data-layout="single">')
w('<div class="cell normal" data-type="normal">')
w('<div class="innerCell">')
w('<h1 id="DIT4ME-Требованиякобъектамсистемы"><span class="numhead-number">8. </span>Требования к объектам системы</h1>')

# 8.1 Request template
w('<h2 id="DIT4ME-Шаблонзапроса(req_template_subj)"><span class="numhead-number">8.1. </span>Шаблон запроса <span class="templateparameter">(req_template_subj)</span></h2>')
w('<div class="table-wrap"><table class="relative-table wrapped confluenceTable" style="width: 37.128%;"><colgroup><col style="width: 37.3511%;"/><col style="width: 62.5716%;"/></colgroup><tbody>')
w('<tr><th scope="col" class="confluenceTh"><p>Параметр</p></th><th scope="col" class="confluenceTh"><p>Описание</p></th></tr>')
w('<tr><td class="confluenceTd"><p>Название шаблона</p></td><td class="confluenceTd"><div class="content-wrapper"><p>' + esc(template_subject) + '</p></div></td></tr>')
w('<tr><td class="confluenceTd"><p>Категория</p></td><td class="confluenceTd"><p>' + esc(category) + '</p></td></tr>')
w('<tr><td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><p>' + ac_link("https://itsm.itsm-qa.mos.ru/ui_extensions/14567", "Карточка расширения UI 14567") + '</p></td></tr>')

# 8.1.2 Rules for request template - list links in table
ar_template = structure["automation_rules"]
rule_links_list = []
for ar in ar_template:
    rule_links_list.append(ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + str(ar["id"]), "Правило " + str(ar["id"])))
w('<tr><td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd"><p>' + '<br/>' + rule_links_list[0] + '</p><p>' + '<br/>' + rule_links_list[1] + '</p><p>' + '<br/>' + rule_links_list[2] + '</p></td></tr>')
w('<tr><td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd"><p>' + ac_link("https://itsm.itsm-qa.mos.ru/workflow_templates/" + str(wf_id), "Карточка РП " + str(wf_id)) + '</p></td></tr>')
w('</tbody></table></div>')

# 8.1.1 UI extension
w('<h3 id="DIT4ME-ТребованиякРасширениюUI"><span class="numhead-number">8.1.1. </span>Требования к Расширению UI</h3>')
w('<p>Расширение UI ' + str(ui_ext_rt["id"]) + ' ' + esc(ui_ext_rt["name"]) + ' (активная версия ' + str(ui_ext_full["active_version"]["id"]) + ') предназначено для сбора списка лиц, которым предоставляется доступ к демо-стенду при регистрации запроса по шаблону. Вкладка "Информация" содержит одно заполняемое поле "Список лиц" (мультивыбор из представления "лица_без_локальных", до 100 записей, обязательное). Остальные поля - служебные скрытые (data-internal, data-hidden).</p>')

# 8.1.2 Automation rules for request template
w('<h3 id="DIT4ME-Требованиякправиламавтоматизации"><span class="numhead-number">8.1.2. </span><span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3>')

# Parse descriptions from desc_*.md files for rules
def parse_rule_desc(ar):
    """Parse a desc_<id>.md file and extract structured info."""
    ar_id = str(ar["id"])
    ar_name = ar["name"]
    ar_trigger = ar["trigger"]
    
    desc_file = "C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_automation_rule_descriptor/artifact/desc_" + ar_id + ".md"
    try:
        with open(desc_file, "r", encoding="utf-8") as f:
            desc_content = f.read()
    except FileNotFoundError:
        return ar_id, ar_name, ar_trigger, [], []
    
    # Extract expressions
    expressions = []
    expr_match = re2.search(r'## Выражения\s*\n\s*<table>(.*?)</table>', desc_content, re2.DOTALL)
    if expr_match:
        expr_table = expr_match.group(1)
        tds = re2.findall(r'<td[^>]*>(.*?)</td>', expr_table, re2.DOTALL)
        for i in range(0, len(tds) - 1, 2):
            name = tds[i].strip().replace('\n', ' ').replace('\r', '')
            logic = tds[i+1].strip().replace('\n', ' ').replace('\r', '')
            expressions.append((name, logic))
    
    # Extract actions
    actions = []
    act_match = re2.search(r'## Действия\s*\n\s*<table>(.*?)</table>', desc_content, re2.DOTALL)
    if act_match:
        act_table = act_match.group(1)
        tds = re2.findall(r'<td[^>]*>(.*?)</td>', act_table, re2.DOTALL)
        for i in range(0, len(tds) - 1, 2):
            action = tds[i].strip().replace('\n', ' ').replace('\r', '')
            action_desc = tds[i+1].strip().replace('\n', ' ').replace('\r', '')
            actions.append((action, action_desc))
    
    return ar_id, ar_name, ar_trigger, expressions, actions

# Rule 10249331
ar_id, ar_name, ar_trigger, exprs, acts = parse_rule_desc({"id": 10249331, "name": "Закрыть запрос если переоткрыли", "trigger": "on status update"})
w('<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + ar_id, "Правило " + ar_id + " — " + esc(ar_name)) + '</p>')
w('<p>Триггер: <code>on status update</code> — при изменении статуса записи.</p>')
w('<p>Условие: <code>was_completed and is_not_completed</code> — запрос раньше был завершён и статус перестал быть "Завершено" (запрос переоткрыт).</p>')
if exprs:
    expr_items = []
    for name, logic in exprs:
        expr_items.append('<li><code>' + esc(name) + '</code> — ' + esc(logic) + '</li>')
    w('<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>')
if acts:
    act_items = []
    for action, action_desc in acts:
        act_items.append('<li>' + esc(action) + ' — ' + esc(action_desc) + '</li>')
    w('<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>')

# Rule 10249443
ar_id, ar_name, ar_trigger, exprs, acts = parse_rule_desc({"id": 10249443, "name": "Создать запрос в Р-Сервис. Заказ демо-стенда (ApiGate 1.0)", "trigger": "on status update"})
w('<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + ar_id, "Правило " + ar_id + " — " + esc(ar_name)) + '</p>')
w('<p>Триггер: <code>on status update</code> — при изменении статуса записи.</p>')
w('<p>Условие: <code>is_wf_pending and !was_wf_pending</code> — запрос перешёл в статус "В рабочем процессе" (workflow_pending), а до изменения этим статусом не был.</p>')
if exprs:
    expr_items = []
    for name, logic in exprs:
        expr_items.append('<li><code>' + esc(name) + '</code> — ' + esc(logic) + '</li>')
    w('<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>')
if acts:
    act_items = []
    for action, action_desc in acts:
        act_items.append('<li>' + esc(action) + ' — ' + esc(action_desc) + '</li>')
    w('<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>')

# Rule 13553013
ar_id, ar_name, ar_trigger, exprs, acts = parse_rule_desc({"id": 13553013, "name": "Завершить после решения от р-сервис", "trigger": "on custom_fields update"})
w('<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + ar_id, "Правило " + ar_id + " — " + esc(ar_name)) + '</p>')
w('<p>Триггер: <code>on custom_fields update</code> — при обновлении пользовательских полей записи.</p>')
w('<p>Условие: <code>note_vendor and request_vendor and !is_completed and note_was_updated</code> — заметка от вендора заполнена, номер запроса вендора заполнен, запрос ещё не завершён, и обновление изменило заметку от вендора.</p>')
if exprs:
    expr_items = []
    for name, logic in exprs:
        expr_items.append('<li><code>' + esc(name) + '</code> — ' + esc(logic) + '</li>')
    w('<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>')
if acts:
    act_items = []
    for action, action_desc in acts:
        act_items.append('<li>' + esc(action) + ' — ' + esc(action_desc) + '</li>')
    w('<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>')

# ===== 8.2 Workflow template =====
w('<h2 id="DIT4ME-ШаблонРабочегопроцесса"><span class="numhead-number">8.2. </span>Шаблон Рабочего процесса</h2>')
w('<h3 id="DIT4ME-ТребованиякРасширениюUI.1"><span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3>')
w('<p>Расширение UI не задано (отсутствует).</p>')
w('<h3 id="DIT4ME-Требованиякправиламавтоматизации.1"><span class="numhead-number">8.2.2. </span><span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3>')
w('<p>' + ac_link("https://itsm.itsm-qa.mos.ru/workflow_templates/" + str(wf_id), "Карточка РП " + str(wf_id)) + '</p>')

# ===== 8.3+ Task templates =====
wf = structure["workflow_template"]
task_templates = wf["task_templates"]
section_num = 2

for tt in task_templates:
    section_num += 1
    tt_id = tt["id"]
    tt_subject = tt["subject"]
    tt_phase = tt.get("phase", "")
    tt_category = tt.get("category", "")
    tt_team = tt.get("team", {}).get("name", "") if tt.get("team") else ""
    
    section_label = 'Шаблон задачи "' + esc(tt_subject) + '"'
    section_id = "DIT4ME-Шаблонзадачи-" + tt_subject.replace(" ", "").replace(".", "").replace(",", "").replace('"', "").replace('"', "")
    
    w('<h2 id="' + section_id + '"><span class="numhead-number">8.' + str(section_num) + '. </span>' + section_label + '</h2>')
    w('<p>' + ac_link("https://itsm.itsm-qa.mos.ru/task_templates/" + str(tt_id), "Карточка шаблона задачи " + str(tt_id)) + '</p>')
    
    phase_info = 'Фаза: ' + esc(tt_phase) + '. Категория: ' + esc(tt_category)
    if tt_team:
        phase_info += '. Ответственная команда: ' + esc(tt_team)
    w('<p>' + esc(phase_info) + '</p>')
    
    # UI Extension
    w('<h3 id="DIT4ME-ТребованиякРасширениюUI-' + str(tt_id) + '"><span class="numhead-number">8.' + str(section_num) + '.1. </span>Требования к Расширению UI</h3>')
    if tt.get("ui_extension"):
        w('<p>' + ac_link("https://itsm.itsm-qa.mos.ru/ui_extensions/" + str(tt["ui_extension"]["id"]), "Карточка расширения UI " + str(tt["ui_extension"]["id"])) + '</p>')
    else:
        w('<p>Расширение UI не задано (отсутствует).</p>')
    
    # Automation rules
    w('<h3 id="DIT4ME-Требованиякправиламавтоматизации-' + str(tt_id) + '"><span class="numhead-number">8.' + str(section_num) + '.2. </span><span>Требования к правилам автоматизации</span></h3>')
    
    if not tt.get("automation_rules"):
        w('<p>Отсутствуют.</p>')
        continue
    
    for ar in tt["automation_rules"]:
        ar_id, ar_name, ar_trigger, exprs, acts = parse_rule_desc(ar)
        w('<p>' + ac_link("https://itsm.itsm-qa.mos.ru/automation_rules/" + ar_id, "Правило " + ar_id + " — " + esc(ar_name)) + '</p>')
        
        # Map trigger to Russian description
        trigger_desc = {
            "on status update": "при изменении статуса записи",
            "on custom_fields update": "при обновлении пользовательских полей записи",
            "after delay": "после задержки по времени",
            "on created": "при создании записи",
            "on note added": "при добавлении комментария",
        }
        trigger_ru = trigger_desc.get(ar_trigger, ar_trigger)
        w('<p>Триггер: <code>' + esc(ar_trigger) + '</code> — ' + esc(trigger_ru) + '.</p>')
        
        # Try to extract condition from description
        # Look for "Условие:" in the desc content
        desc_file = "C:/Alex/_PRJ/2_MosITSM Automation Prj/mos_itsm_automation_rule_descriptor/artifact/desc_" + ar_id + ".md"
        try:
            with open(desc_file, "r", encoding="utf-8") as f:
                full_desc = f.read()
            cond_match = re2.search(r'Условие\s*\n\s*<td>(.*?)</td>', full_desc, re2.DOTALL)
            if cond_match:
                cond_text = cond_match.group(1).strip().replace('\n', ' ')
                w('<p>Условие: ' + esc(cond_text) + '</p>')
        except:
            pass
        
        if exprs:
            expr_items = []
            for name, logic in exprs:
                expr_items.append('<li><code>' + esc(name) + '</code> — ' + esc(logic) + '</li>')
            w('<p>Выражения:</p><ul>' + '\n'.join(expr_items) + '</ul>')
        if acts:
            act_items = []
            for action, action_desc in acts:
                act_items.append('<li>' + esc(action) + ' — ' + esc(action_desc) + '</li>')
            w('<p>Действия:</p><ul>' + '\n'.join(act_items) + '</ul>')

# Close section 8 and document
w('</div></div></div>')
w('</div></div>')
w('</ac:rich-text-body>')

page_body = '\n'.join(L)

with open("page_body_8170964_final.html", "w", encoding="utf-8") as f:
    f.write(page_body)

print("Page body written: " + str(len(page_body)) + " bytes")

# Validate tag balance
stack = []
for m in re2.finditer(r'<(/?)(\w+)((?:\s+[^>"\']*(?:"[^"]*"|\'[^\']*\')*)?)>', page_body):
    slash, tag, attrs = m.group(1), m.group(2), m.group(3)
    is_void = tag in ['img', 'br', 'hr', 'col', 'colgroup', 'input', 'ri:url', 'ri:user', 'ac:link-body']
    
    if slash:
        if stack and stack[-1] == tag:
            stack.pop()
        else:
            print("WARNING: Unexpected close: </" + tag + "> at pos " + str(m.start()))
    else:
        if not is_void:
            stack.append(tag)

if stack:
    print("WARNING: Unclosed tags: " + str(stack))
else:
    print("OK: All tags balanced!")

# Check ac:link blocks have text
ac_links = re2.findall(r'<ac:link>(.*?)</ac:link>', page_body, re2.DOTALL)
for i, block in enumerate(ac_links):
    if 'plain-text-body' not in block:
        print("WARNING: ac:link " + str(i) + " has no plain-text-body")
    elif re2.search(r'<ac:plain-text-body>\s*</ac:plain-text-body>', block):
        print("WARNING: ac:link " + str(i) + " has empty plain-text-body")

print("ac:link blocks checked: " + str(len(ac_links)))
