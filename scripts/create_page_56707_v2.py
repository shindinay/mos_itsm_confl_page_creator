#!/usr/bin/env python3
"""Создание страницы Confluence для шаблона запроса 56707.

Подход: строим тело страницы заново из template_body.html, аккуратно
подставляя данные МосИТСМ в плейсхолдеры и вставляя разделы задач
внутрь существующей структуры, без лишних <div>.
"""
import json
import os
import re
import html as html_mod
import urllib.request
import urllib.error
from datetime import datetime

# --- Config ---
ENV_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
TEMPLATE_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\template_body.html"
STRUCT_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_get_obj_structure\artifact\structure_56707_20261028_193811.json"
DESC_DIR = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\artifact"
BACKUPS_DIR = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\backups"

with open(ENV_FILE, encoding="utf-8-sig") as f:
    env = json.load(f)

base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]
space_key = "DIT4ME"

with open(STRUCT_FILE, encoding="utf-8") as f:
    structure = json.load(f)

rt = structure["request_template"]
wf = structure["workflow_template"]

TEMPLATE_ID = 56707
template_subject = rt.get("localized_subject") or rt.get("subject", "Шаблон " + str(TEMPLATE_ID))
template_category = rt.get("category", "")
template_uiext = rt.get("ui_extension", {})
template_uiext_id = template_uiext.get("id") if template_uiext else None
template_uiext_name = template_uiext.get("name", "")
wf_id = wf.get("id") if wf else None
wf_subject = wf.get("subject", "") if wf else ""

userkey = "2c98d8026e1c34cb016e45ea6c064b40"

# --- Helpers ---
def read_md(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

def read_rule_json(rid):
    """Попытка прочитать JSON правила из backups."""
    backup_path = os.path.join(BACKUPS_DIR, f"rule_{rid}.json")
    if os.path.exists(backup_path):
        with open(backup_path, encoding="utf-8") as f:
            return json.load(f)
    return None

def rule_xhtml(rid):
    """Описание одного правила автоматизации."""
    desc_path = os.path.join(DESC_DIR, f"desc_{rid}.md")
    if os.path.exists(desc_path):
        md_text = read_md(desc_path)
        if md_text:
            return md_to_xhtml(md_text)
    rule = read_rule_json(rid)
    if rule:
        name = rule.get("name", "правило " + str(rid))
        trigger = rule.get("trigger", "")
        desc = rule.get("description", "")
        parts = [f"<p><strong>ID:</strong> {rid}</p>"]
        parts.append(f"<p><strong>Название:</strong> {html_mod.escape(name)}</p>")
        parts.append(f"<p><strong>Триггер:</strong> {html_mod.escape(trigger)}</p>")
        if desc:
            parts.append(f"<p><strong>Описание:</strong> {html_mod.escape(desc)}</p>")
        return "\n".join(parts)
    return f"<p>ID {rid} — описание не найдено</p>"

def md_to_xhtml(md_text):
    if not md_text:
        return "<p>Описание отсутствует</p>"
    lines = md_text.split("\n")
    blocks = []
    current_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            blocks.append('<h4>' + html_mod.escape(stripped[2:]) + '</h4>')
        elif stripped.startswith("## "):
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            blocks.append('<h5>' + html_mod.escape(stripped[3:]) + '</h5>')
        elif stripped.startswith("### "):
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            blocks.append('<h6>' + html_mod.escape(stripped[4:]) + '</h6>')
        elif stripped == "":
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
        elif '<table>' in line or '<table ' in line or '</table>' in line or '<tr>' in line or '</tr>' in line or '<th>' in line or '</th>' in line or '<td>' in line or '</td>' in line:
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            blocks.append(line)
        else:
            current_lines.append(stripped)
    if current_lines:
        blocks.append("\n".join(current_lines))
    result = []
    for block in blocks:
        stripped = block.strip()
        if stripped.startswith('<h4>') or stripped.startswith('<h5>') or stripped.startswith('<h6>'):
            result.append(block)
        elif stripped.startswith('<table'):
            result.append(block)
        else:
            text = " ".join(stripped.split())
            if text:
                if '<table' in text or '<strong>' in text or '<em>' in text:
                    result.append('<p>' + text + '</p>')
                else:
                    result.append('<p>' + html_mod.escape(text) + '</p>')
    return "\n".join(result)

def build_uiext_desc(uiext_data):
    """Описание UI расширения из JSON."""
    if not uiext_data or uiext_data.get("error"):
        return "<p>Отсутствует</p>"
    name = uiext_data.get("name", "")
    title = uiext_data.get("title", "")
    ext_id = uiext_data.get("id", "?")
    cat = uiext_data.get("category", "")
    created = uiext_data.get("created_at", "")
    updated = uiext_data.get("updated_at", "")
    parts = [f"<p><strong>Название:</strong> {html_mod.escape(name)}</p>"]
    parts.append(f"<p><strong>ID:</strong> {ext_id}</p>")
    parts.append(f"<p><strong>Категория:</strong> {html_mod.escape(cat)}</p>")
    parts.append(f"<p><strong>Заголовок:</strong> {html_mod.escape(title)}</p>")
    parts.append(f"<p><strong>Создано:</strong> {created}</p>")
    parts.append(f"<p><strong>Обновлено:</strong> {updated}</p>")
    tabs = uiext_data.get("tabs")
    if tabs:
        html_c = tabs.get("html") or ""
        js_c = tabs.get("javascript") or ""
        css_c = tabs.get("css") or ""
        if html_c:
            parts.append(f"<p><strong>HTML:</strong> {len(html_c)} символов</p>")
        if js_c:
            parts.append(f"<p><strong>JavaScript:</strong> {len(js_c)} символов</p>")
        if css_c:
            parts.append(f"<p><strong>CSS:</strong> {len(css_c)} символов</p>")
    return "\n".join(parts)

# --- Load template ---
with open(TEMPLATE_FILE, encoding="utf-8") as f:
    body = f.read()

# --- Task templates from workflow ---
tasks = wf.get("task_templates", []) if wf else []

# Build task template content (without wrapping <div>)
task_content_parts = []
for task in tasks:
    tid = task.get("id")
    tsubject = task.get("subject", "Задача " + str(tid))
    tphase = task.get("phase", "")
    section_id = f"DIT4ME-Задача{tid}"
    # Use phase number from task order
    task_num = tasks.index(task) + 1
    phase_short = tphase.replace(" ", "").lower()[:10]

    section = f'<h2 id="{section_id}"><span class="numhead-number">{task_num}. </span>{html_mod.escape(tphase)}: {html_mod.escape(tsubject)}</h2>'

    # 9.2.1 UI extension
    tuix = task.get("ui_extension")
    if tuix and not tuix.get("error"):
        section += f'<h3 id="UI{tid}"><span class="numhead-number">{task_num}.1. </span>Требования к Расширению UI</h3>\n'
        section += build_uiext_desc(tuix)
    else:
        section += f'<h3 id="UI{tid}"><span class="numhead-number">{task_num}.1. </span>Требования к Расширению UI</h3>\n'
        section += "<p>Отсутствует</p>"

    # 9.2.2 Automation rules
    trules = task.get("automation_rules", [])
    section += f'<h3 id="AR{tid}"><span class="numhead-number">{task_num}.2. </span>Требования к правилам автоматизации</h3>\n'
    if trules:
        section += f"<p>На задаче {tid} определено {len(trules)} правил автоматизации:</p>\n<ul>\n"
        for rule in trules:
            rid = rule.get("id")
            rname = rule.get("name", "правило " + str(rid))
            link = f"https://itsm.itsm-qa.mos.ru/automation_rules/{rid}"
            section += f"<li><a href=\"{link}\">{html_mod.escape(rname)}</a> (ID {rid})</li>\n"
        section += "</ul>\n"
        # Detailed descriptions for each rule
        for rule in trules:
            rid = rule.get("id")
            rname = rule.get("name", str(rid))
            section += f'<h3 id="ARDesc{rid}"><span class="numhead-number">{task_num}.2. </span>Правило {rid}: {html_mod.escape(rname)}</h3>\n'
            section += rule_xhtml(rid)
            section += "\n"
    else:
        section += "<p>Правила автоматизации отсутствуют</p>"

    task_content_parts.append(section)

task_content_html = "\n\n".join(task_content_parts)

# --- Now rebuild the page body more carefully ---
# Strategy: take template_body, find the end of section 9.2.2 placeholder
# and insert task content there, BUT keeping only raw content (no <div> wrappers)

# Find where to insert: after the last </p></div> of section 9.2.2 placeholder
# Actually, let's find the </div> that closes section 9 and insert before it

# The template ends with the section 9.2 block that closes with </div></div></div></div>
# We want to insert task content inside the existing innerCell div

# Find the section 9.2.2 placeholder's closing </div>
# Pattern: section 9.2 ends with <h3 id="DIT4ME-Требованиякправиламавтоматизации.1">...
# followed by </div></div></div>

# Let's be surgical: find the last </div> that closes the section 9 area
# and insert task content before it

# The structure is:
# <div class="columnLayout single" ...>  <-- section 9 wrapper
#   <div class="cell normal" ...>
#     <div class="innerCell">
#       <h2>...Шабло задачи...</h2>
#       <h3>...8.2.1...</h3>
#       <h3>...8.2.2...</h3>
#     </div>
#   </div>
# </div>

# Find the innerCell of section 9
# We know it starts with the h2 containing "Шаблон задачи" or "task_template_name"
# and ends before the last </div></div></div>

# Approach: find the last </div> in the file and insert task content before it
# But we need to be careful about nesting

# Actually, the simplest approach: find the position after section 9.2.2 placeholder's </p>
# and insert content there, inside the same innerCell

# Find: <h3 id="DIT4ME-Требованиякправиламавтоматизации.1">... last h3 of section 9.2
# Then find the </p> that follows (the placeholder content)
# Then insert our task content after that </p>

# Actually the task content needs to replace the section 9.2 placeholder entirely
# Let's find the section 9.2.2 h3 and replace it plus insert tasks after

# Find position of the last h3 in the template (section 9.2.2)
# and insert task content after it and its paragraph

# Let's find the pattern: the h3 with "Требования к правилам автоматизации" at the end
# and replace it

pattern = r'(<h3[^>]*id="DIT4ME-Требованиякправиламавтоматизации\.1"[^>]*>.*?</h3>)\s*(<p[^>]*>.*?</p>)'
match = re.search(pattern, body, re.DOTALL)
if match:
    h3_tag = match.group(1)
    insert_after = match.end()
    body = body[:insert_after] + "\n\n" + task_content_html + body[insert_after:]
else:
    # Fallback: insert before the final </div> of section 9
    # Find last </div> in the file
    body = body.replace("</div>\n</div>\n</div>\n</div>\n</div>\n", "\n" + task_content_html + "\n</div>\n</div>\n</div>\n</div>\n</div>\n")

# --- Now do all simple replacements ---
template_uri = f"https://itsm.itsm-qa.mos.ru/request_templates/{TEMPLATE_ID}"

# History section
body = re.sub(r'\*\*req_uri\*\*', template_uri, body)
body = re.sub(r'\*\*req_created_at\*\*', datetime.now().strftime("%d.%m.%Y %H:%M"), body)
# Author
body = re.sub(r'<p>\*\*\s*\*\*</p>', '<p><em>ИИ-агент ZCode</em></p>', body)

# Section 3 - req_subject
body = re.sub(r'<p>\*\*req_subject\*\*</p>', f"<p>{html_mod.escape(template_subject)}</p>", body)
# req_uri in section 3
body = re.sub(r'<p>\*\*req_uri\*\*</p>', f"<p>{template_uri}</p>", body)
body = re.sub(r'\*\*req_template_account\*\*', "Каталог услуг Правительства Москвы (itsm)", body)

# Section 8.1
body = re.sub(r'\*\*req_template_subj\*\*', html_mod.escape(template_subject), body)
body = re.sub(r'\*\*req_template_category\*\*', html_mod.escape(template_category), body)

# UI extension link
uiext_link = f"ui_extension/{template_uiext_id} — {html_mod.escape(template_uiext_name or str(template_uiext_id))}" if template_uiext_id else "Отсутствует"
body = re.sub(r'\*\*req_template_ui_extension_link\*\*', f"<p>{html_mod.escape(uiext_link)}</p>", body)

# AR link (none at template level)
body = re.sub(r'\*\*req_ar_link\*\*', "<p>На уровне шаблона запроса правила автоматизации отсутствуют</p>", body)

# UI extension description
body = re.sub(r'\*\*req_template_ui_extension_description\*\*', build_uiext_desc(template_uiext) if template_uiext and not template_uiext.get("error") else "<p>Отсутствует</p>", body)

# Workflow template name in section 9 table
body = re.sub(r'<p>\*\*req_template_subj\*\*</p>', f"<p>{html_mod.escape(wf_subject)}</p>", body)
body = re.sub(r'<p>\*\*req_template_category\*\*</p>', f"<p>{html_mod.escape(template_category)}</p>", body)

# Workflow UI extension link
body = re.sub(r'\*\*req_template_ui_extension_link\*\*', f"<p>{html_mod.escape(uiext_link)}</p>", body)
body = re.sub(r'\*\*req_ar_link\*\*', "<p>На уровне шаблона РП правила автоматизации отсутствуют</p>", body)

# Workflow variable placeholders
body = re.sub(
    r'<input[^>]*name="variableValues\.wf_ui_ext_desc"[^>]*/?>[^<]*</span>',
    f"<p>{html_mod.escape('Отсутствует')}</p>",
    body
)
body = re.sub(
    r'<input[^>]*name="variableValues\.wf_ar_desc"[^>]*/?>[^<]*</span>',
    "<p>На уровне шаблона рабочего процесса правила автоматизации отсутствуют. Правила определены на задачах внутри РП (см. раздел 9.2).</p>",
    body
)

# task_template_name placeholder
body = re.sub(
    r'<input[^>]*name="variableValues\.task_template_name"[^>]*/?>[^<]*</span>',
    f"Список всех {len(tasks)} задач РП (см. разделы 9.2.x ниже)",
    body
)

# Author macro
author_macro = '<ac:structured-macro ac:name="profile"><ac:parameter ac:name="user"><ri:user ri:userkey="' + userkey + '" /></ac:parameter></ac:parameter>'
body = re.sub(
    r'(<td class="highlight-#f4f5f7 confluenceTd"[^>]*><strong[^>]*>Автор</strong>[^<]*<p><span[^>]*><span><em><span[^>]*><img[^>]*/></span></em></span></span></p></td>)',
    '<td class="highlight-#f4f5f7 confluenceTd"><p>' + author_macro + '</p></td>',
    body, count=1
)

# Fix enableNumbering
body = re.sub(
    r'<h1[^>]*id="[^"]*"[^>]*><span[^>]*>\{&quot;enableNumbering&quot;:true\}</span>\s*\</h1>',
    '<h1><span class="numhead-number">2. </span>Определения и сокращения</h1>',
    body, count=1
)
body = re.sub(
    r'<li><a href="[^"]*enableNumbering[^"]*">\{&quot;enableNumbering&quot;:true\}</a></li>',
    '<li><a href="#Определенияисокращения">2. Определения и сокращения</a></li>',
    body, count=1
)
body = re.sub(
    r"href='#TemplatePreview-\{&quot;enableNumbering&quot;:true\}'",
    "href='#Определенияисокращения'",
    body
)

# Fix img tags
body = re.sub(r'<img([^>]*)>', lambda m: '<img' + m.group(1).rstrip() + '/>', body)

# --- Debug: save and check ---
output_file = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\page_body_56707.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(body)
print(f"Page body saved: {output_file} ({len(body)} chars)")

# Quick XHTML balance check
open_divs = body.count('<div ') - body.count('</div>')
open_tables = body.count('<table') - body.count('</table>')
print(f"Unbalanced <div>: {open_divs}, <table>: {open_tables}")

# --- Build payload ---
page_title = f"Требования к шаблону запроса {TEMPLATE_ID} — {template_subject}"
payload = {
    "type": "page",
    "title": page_title,
    "space": {"key": space_key},
    "body": {"storage": {"value": body, "representation": "storage"}},
}

# Try publishing
req = urllib.request.Request(
    base + "/rest/api/content",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    page_id = result["id"]
    page_url = result["_links"]["base"] + result["_links"]["webui"]
    print(f"SUCCESS! Page ID: {page_id}")
    print(f"Page URL: {page_url}")
    print(f"Page title: {page_title}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    err_body = e.read().decode("utf-8")
    print(err_body[:2000])
    # Save for debugging
    debug_file = output_file.replace(".html", "_debug.html")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Debug body saved: {debug_file}")
except Exception as e:
    print(f"Error: {e}")
