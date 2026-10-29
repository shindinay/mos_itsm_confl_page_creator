#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build page body for RFC 56363 - MosITSM. Provision access to demo stand.
Reads the template, replaces placeholders, and writes the filled page body.
"""
import json
import re
import os
import html as html_mod

BASE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj"
CONF = os.path.join(BASE, "mos_itsm_confl_page_creator")
ARTIFACT = os.path.join(BASE, "mos_itsm_get_obj_structure", "artifact")

# Load template
with open(os.path.join(CONF, "page_body.html"), encoding="utf-8") as f:
    html = f.read()

# --- Variable values ---
req_id = "56363"
req_uri = "https://itsm.itsm-qa.mos.ru/requests/56363"
req_subject = "МосИТСМ. Предоставление доступа к демо стенду"
req_requested_for = "Наумова Елена Станиславовна"
req_created_at = "2021-10-25T16:30:27+03:00"
req_first_comment = "2021-10-25T16:30:27+03:00 | Наумова Елена Станиславовна: Тема: Восстановить пароль доступа сотруднику структурного подразделения\nКому: 4me_inbound+eps.its@it.mos.ru"
req_template_subj = "МосИТСМ. Предоставление доступа к демо стенду"
req_template_account = "itsm-qa.mos.ru"
confluence_token_owner = '2c98d8026e1c34cb016e45ea6c064b40'

# --- Replace input fields (req_id, req_subject, req_template_subj, req_requested_for, req_created_at, req_first_comment) ---
# Pattern: <input ... disabled=""/> <span class="templateparameter">(...)</span>
placeholder_pattern = re.compile(
    r'<input[^>]*class="page-template-field"[^>]*>.*?<span class="templateparameter">\([^)]+\)</span>',
    re.DOTALL
)

def replace_inputs(text, new_value):
    """Replace all remaining placeholder inputs with the new value."""
    return placeholder_pattern.sub(new_value, text)

# First pass: identify which specific inputs we need to replace
# We need to find and replace each individually because there are multiple inputs

# Pattern for each named input
input_pattern = re.compile(
    r'<input type="text" name="variableValues\.(' + re.escape('req_') + r'[a-z_]+)"[^>]*/>.*?<span class="templateparameter">\([^)]+\)</span>',
    re.DOTALL
)

# More targeted: replace each input+span pair individually
# req_id
html = re.sub(
    r'<input type="text" name="variableValues\.req_id" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_id\)</span>',
    req_id, html)

# req_subject
html = re.sub(
    r'<input type="text" name="variableValues\.req_subject" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_subject\)</span>',
    req_subject, html)

# req_template_subj
html = re.sub(
    r'<input type="text" name="variableValues\.req_template_subj" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_template_subj\)</span>',
    req_template_subj, html)

# req_requested_for
html = re.sub(
    r'<input type="text" name="variableValues\.req_requested_for" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_requested_for\)</span>',
    req_requested_for, html)

# req_created_at (inside a span with style)
html = re.sub(
    r'<span style="color: rgb\(0,0,0\);"> <input type="text" name="variableValues\.req_created_at" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_created_at\)</span></span>',
    req_created_at, html)

# req_first_comment
html = re.sub(
    r'<input type="text" name="variableValues\.req_first_comment" size="12" class="page-template-field" disabled=""/>'
    r' <span class="templateparameter">\(req_first_comment\)</span>',
    req_first_comment, html)

# --- Replace template-variable images ---

# req_uri -> visible hyperlink
html = html.replace(
    '<span class="confluence-embedded-file-wrapper">'
    '<img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" '
    'src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_uri" '
    'data-image-src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_uri"/>'
    '</span>',
    '<a href="' + req_uri + '">RFC ' + req_id + '</a>'
)

# req_template_account
html = html.replace(
    '<span class="confluence-embedded-file-wrapper">'
    '<img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" '
    'src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_template_account" '
    'data-image-src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=req_template_account"/>'
    '</span>',
    req_template_account
)

# confluence_token_owner -> @-mention (inside <em> wrapper)
html = html.replace(
    '<span style="color: rgb(112,112,112);"><span><em>'
    '<span class="confluence-embedded-file-wrapper">'
    '<img class="confluence-embedded-image template-variable confluence-external-resource" draggable="false" '
    'src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=confluence_token_owner" '
    'data-image-src="https://itpm-wiki.mos.ru/plugins/servlet/confluence/placeholder/template-variable?name=confluence_token_owner"/>'
    '</span></em></span></span>',
    '<ac:link><ac:link-body><ri:user ri:userkey="' + confluence_token_owner + '"/></ac:link-body></ac:link>'
)

# Replace remaining placeholder inputs with "(не задано)"
remaining_inputs = re.findall(
    r'<input type="text" name="variableValues\.[^"]*"[^>]*/>'
    r' <span class="templateparameter">\([^)]+\)</span>', html)
for inp in remaining_inputs:
    name_m = re.search(r'name="variableValues\.([^"]+)"', inp)
    name = name_m.group(1) if name_m else "unknown"
    html = html.replace(inp, "(не задано)")

# --- Now build the sections 8.1 and 8.2 with automation rule descriptions ---

# Read the full structure data
with open(os.path.join(ARTIFACT, "structure_56363_20261028_182232.json"), encoding="utf-8") as f:
    structure = json.load(f)

template = structure["request_template"]

# UI Extension for template
ui_ext = template.get("ui_extension", {})
ui_ext_id = ui_ext.get("id", "")
ui_ext_name = ui_ext.get("name", "")
ui_ext_title = ui_ext.get("title", "")
ui_ext_html = ui_ext.get("html", "")

# Automation rules for template (top-level)
template_rules = template.get("automation_rules", [])

# Workflow
workflow = template.get("workflow_template", {})
workflow_subject = workflow.get("subject", "")

# Task templates
task_templates = workflow.get("task_templates", [])

# --- Build 8.1.1: UI Extension description for template ---
# Build a concise description of the UI extension HTML
def describe_ui_extension(ext_id, ext_name, ext_title, ext_html):
    """Generate a description of the UI extension from its HTML."""
    if not ext_html:
        return "<p>Расширение UI отсутствует.</p>"

    lines = []
    lines.append("<p>")
    lines.append("<ac:link><ri:url ri:value=\"https://itsm.itsm-qa.mos.ru/ui_extensions/" + str(ext_id) + "\" />")
    lines.append("<ac:plain-text-body>Карточка расширения UI " + str(ext_id) + ": " + ext_name + "</ac:plain-text-body></ac:link>")
    lines.append("</p>")
    lines.append("<table class=\"relative-table wrapped confluenceTable\"><colgroup><col style=\"width: 30%;\"/><col style=\"width: 70%;\"/></colgroup><tbody>")
    lines.append("<tr><th class=\"confluenceTh\"><p>Заголовок вкладки</p></th><td class=\"confluenceTd\"><p>" + ext_title + "</p></td></tr>")

    # Parse fields from HTML
    import re as re2
    fields = re2.findall(r'data-field="([^"]+)"', ext_html)
    if fields:
        lines.append("<tr><th class=\"confluenceTh\"><p>Поля формы</p></th><td class=\"confluenceTd\"><p>" + ", ".join(fields) + "</p></td></tr>")

    # Custom view / suggest
    suggests = re.findall(r'data-suggest-url="([^"]+)"', ext_html)
    if suggests:
        lines.append("<tr><th class=\"confluenceTh\"><p>Подсказки</p></th><td class=\"confluenceTd\"><p>" + suggests[0] + "</p></td></tr>")

    # data-max, data-multiple
    max_m = re.search(r'data-max="(\d+)"', ext_html)
    if max_m:
        lines.append("<tr><th class=\"confluenceTh\"><p>Макс. количество</p></th><td class=\"confluenceTd\"><p>" + max_m.group(1) + " лиц</p></td></tr>")

    lines.append("</tbody></table>")
    lines.append("<p><strong>HTML вкладки:</strong></p>")
    lines.append("<pre>" + html_mod.escape(ext_html) + "</pre>")
    return "\n".join(lines)

ui_ext_desc = describe_ui_extension(ui_ext_id, ui_ext_name, ui_ext_title, ui_ext_html)

# --- Build 8.1.2: Automation rules for template ---
def describe_rule(rule):
    """Generate description for one automation rule per description_template.md."""
    rid = rule.get("id", "")
    rname = rule.get("name", "")
    trigger = rule.get("trigger", "")
    condition = rule.get("condition", "")
    expressions = rule.get("expressions", [])
    actions = rule.get("actions", {})

    lines = []
    lines.append("<p>")
    lines.append("<ac:link><ri:url ri:value=\"https://itsm.itsm-qa.mos.ru/automation_rules/" + str(rid) + "\" />")
    lines.append("<ac:plain-text-body>Карточка правила " + str(rid) + ": " + html_mod.escape(rname) + "</ac:plain-text-body></ac:link>")
    lines.append("</p>")

    # Настройки правила
    lines.append("<table class=\"relative-table wrapped confluenceTable\"><colgroup><col style=\"width: 30%;\"/><col style=\"width: 70%;\"/></colgroup><tbody>")
    lines.append("<tr><td class=\"confluenceTd\"><strong>Триггер</strong></td><td class=\"confluenceTd\">" + trigger + "</td></tr>")
    lines.append("<tr><td class=\"confluenceTd\"><strong>Условие</strong></td><td class=\"confluenceTd\"><code>" + html_mod.escape(condition) + "</code></td></tr>")
    lines.append("</tbody></table>")

    # Выражения
    if expressions:
        lines.append("<table class=\"relative-table wrapped confluenceTable\"><colgroup><col style=\"width: 40%;\"/><col style=\"width: 60%;\"/></colgroup><tbody>")
        lines.append("<tr><th class=\"confluenceTh\"><p>Имя выражения</p></th><th class=\"confluenceTh\"><p>Логика</p></th></tr>")
        for e in expressions:
            ename = e.get("name", "")
            eexpr = e.get("expression", "")
            # Shorten long expressions
            if len(eexpr) > 150:
                eexpr = html_mod.escape(eexpr[:150]) + " ..."
            else:
                eexpr = html_mod.escape(eexpr)
            lines.append("<tr><td class=\"confluenceTd\"><p>" + html_mod.escape(ename) + "</p></td>")
            lines.append("<td class=\"confluenceTd\"><p><code>" + eexpr + "</code></p></td></tr>")
        lines.append("</tbody></table>")

    # Actions
    if actions:
        lines.append("<table class=\"relative-table wrapped confluenceTable\"><colgroup><col style=\"width: 40%;\"/><col style=\"width: 60%;\"/></colgroup><tbody>")
        lines.append("<tr><th class=\"confluenceTh\"><p>Действие</p></th><th class=\"confluenceTh\"><p>Описание</p></th></tr>")
        for k, v in actions.items():
            vstr = str(v)
            if len(vstr) > 200:
                vstr = html_mod.escape(vstr[:200]) + " ..."
            else:
                vstr = html_mod.escape(vstr)
            lines.append("<tr><td class=\"confluenceTd\"><p><code>" + html_mod.escape(k) + "</code></p></td>")
            lines.append("<td class=\"confluenceTd\"><p>" + vstr + "</p></td></tr>")
        lines.append("</tbody></table>")

    return "\n".join(lines)

# Rules for template
template_rules_html = ""
for i, r in enumerate(template_rules, 1):
    template_rules_html += "<h4 id=\"DIT4ME-Требованиякправиламм автоматизации." + str(i) + "\"><span class=\"numhead-number\">8.1.2." + str(i) + ". </span>Требования к правилу автоматизации " + str(i) + " - " + html_mod.escape(r.get('name','')) + "</h4>"
    template_rules_html += describe_rule(r)
    template_rules_html += "<p><br/></p>"

# Rules for each task template in workflow
workflow_rules_html = ""
task_sections_html = ""
num = 1
for tt in task_templates:
    tt_id = tt.get("id", "")
    tt_subject = tt.get("subject", "")
    tt_phase = tt.get("phase", "")
    tt_failure = tt.get("failure_task_template")

    task_sections_html += '<h3 id="DIT4ME-Шаблонзадачи' + str(tt_id) + '"><span class="numhead-number">8.2.' + str(num) + '. </span>Шаблон задачи ' + html_mod.escape(tt_subject) + '</h3>'

    # UI Extension for task template
    tt_ui = tt.get("ui_extension")
    if tt_ui:
        task_sections_html += '<h4 id="DIT4ME-ТребованиякРасширениюUI.тз' + str(tt_id) + '"><span class="numhead-number">8.2.' + str(num) + '.1. </span>Требования к Расширению UI ' + tt_ui.get('name','') + '</h4>'
        task_sections_html += '<p><ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/ui_extensions/' + str(tt_ui.get("id","")) + '" /><ac:plain-text-body>Карточка расширения UI ' + str(tt_ui.get("id","")) + '</ac:plain-text-body></ac:link></p>'
    else:
        task_sections_html += '<h4 id="DIT4ME-ТребованиякРасширениюUI.тз' + str(tt_id) + '"><span class="numhead-number">8.2.' + str(num) + '.1. </span>Требования к Расширению UI</h4>'
        task_sections_html += '<p>Отсутствует</p>'

    # Automation rules for task template
    tt_rules = tt.get("automation_rules", [])
    if tt_rules:
        for j, r in enumerate(tt_rules, 1):
            task_sections_html += '<h4 id="DIT4ME-Требованиякправиламм' + str(r.get("id","")) + '"><span class="numhead-number">8.2.' + str(num) + '.' + str(j) + '. </span>Требования к правилу автоматизации ' + str(j) + ' - ' + html_mod.escape(r.get("name", "")) + '</h4>'
            task_sections_html += describe_rule(r)
            task_sections_html += '<p><br/></p>'
    else:
        task_sections_html += '<h4 id="DIT4ME-Требованиякправиламм' + str(tt_id) + '"><span class="numhead-number">8.2.' + str(num) + '.1. </span>Требования к правилам автоматизации</h4>'
        task_sections_html += '<p>Отсутствуют</p>'

    if tt_failure:
        task_sections_html += '<p><strong>Задача при сбое:</strong> ' + html_mod.escape(tt_failure.get("name", "")) + ' (ID: ' + str(tt_failure.get("id", "")) + ')</p>'

    num += 1

# Update workflow rules with task template rules
workflow_rules_html = task_sections_html

# --- Replace section placeholders ---

# 8.1.1: UI Extension
html = re.sub(
    r'<h3 id="DIT4ME-ТребованиякРасширениюUI"[^>]*>.*?</h3>\s*<p>.*?</p>',
    '<h3 id="DIT4ME-ТребованиякРасширениюUI">'
    '<span class="numhead-number">8.1.1. </span>Требования к Расширению UI</h3>'
    + ui_ext_desc,
    html, flags=re.DOTALL
)

# 8.1.2: Template automation rules
html = re.sub(
    r'<h3 id="DIT4ME-Требованиякправиламавтоматизации"[^>]*>.*?</h3>\s*<p>.*?</p>',
    '<h3 id="DIT4ME-Требованиякправиламавтоматизации">'
    '<span class="numhead-number">8.1.2. </span>Требования к правилам автоматизации</h3>'
    + template_rules_html,
    html, flags=re.DOTALL
)

# 8.2: Workflow rules + task templates
html = re.sub(
    r'<h3 id="DIT4ME-ТребованиякРасширениюUI\.1"[^>]*>.*?</h3>\s*<p>.*?</p>\s*'
    r'<h3 id="DIT4ME-Требованиякправиламавтоматизации\.1"[^>]*>.*?</h3>\s*<p>.*?</p>',
    '<h3 id="DIT4ME-ТребованиякРасширениюUI.1">'
    '<span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3>'
    '<p>Расширения UI у задач рабочего процесса отсутствуют.</p>'
    '<h3 id="DIT4ME-Требованиякправиламавтоматизации.1">'
    '<span class="numhead-number">8.2.2. </span>Требования к правилам автоматизации</h3>'
    + workflow_rules_html,
    html, flags=re.DOTALL
)

# 8.3: Remove the generic task template placeholder (replaced by per-task subsections)
html = re.sub(
    r'<h2 id="DIT4ME-Шаблонзадачи[^"]*"[^>]*>.*?</h2>',
    '',  # Remove, replaced by individual task sections in 8.2.N
    html, flags=re.DOTALL
)

# --- Fix TOC ---
# Remove old 8.2.1, 8.2.2 entries and 8.3 entries from TOC, replace with task template entries
old_toc_li = re.search(
    r"<li><a href='#TemplatePreview-ШаблонРабочегопроцесса'>8\.2\. Шаблон Рабочего процесса</a>\s*"
    r"<ul class='toc-indentation'>.*?</ul>\s*</li>\s*"
    r"<li><a href='#TemplatePreview-Шаблонзадачи'>8\.3\. Шаблон задачи</a>.*?</li>",
    html, flags=re.DOTALL
)
if old_toc_li:
    new_toc_items = "<li><a href='#TemplatePreview-ШаблонРабочегопроцесса'>8.2. Шаблон Рабочего процесса</a><ul class='toc-indentation'>"
    num = 1
    for tt in task_templates:
        new_toc_items += "<li><a href='#DIT4ME-Шаблонзадачи" + str(tt.get('id','')) + "'>" + str(num) + ".2. " + tt.get('subject', '') + "</a></li>"
        num += 1
    new_toc_items += "</ul></li>"
    html = html.replace(old_toc_li.group(0), new_toc_items)

# --- Save result ---
out_path = os.path.join(CONF, "page_body_56363_filled.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Saved to {out_path}")
print(f"File size: {os.path.getsize(out_path)} bytes")

# Check remaining placeholders
remaining = re.findall(r'template-variable\?name=([^"\']+)', html)
if remaining:
    print("WARNING: Remaining placeholders:", remaining)
else:
    print("All placeholders replaced successfully.")

# Check for empty ac:link
empty_links = re.findall(r'<ac:link>(?:(?!<ac:plain-text-body>).)*?</ac:link>', html)
for el in empty_links:
    if '<ac:plain-text-body>' not in el:
        print("WARNING: Empty ac:link found:", el[:100])
