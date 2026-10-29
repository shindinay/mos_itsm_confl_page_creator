#!/usr/bin/env python3
"""Создание страницы Confluence для шаблона запроса 56707."""
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

# --- Data ---
TEMPLATE_ID = 56707
template_subject = rt.get("localized_subject") or rt.get("subject", "Шаблон " + str(TEMPLATE_ID))
template_category = rt.get("category", "")
template_uiext_id = rt.get("ui_extension", {}).get("id") if rt.get("ui_extension") else None
template_uiext_name = rt.get("ui_extension", {}).get("name", "")
wf_id = wf.get("id") if wf else None
wf_subject = wf.get("subject", "") if wf else ""
service_name = (rt.get("service") or {}).get("name", "")

now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

# Confluence userkey for author
userkey = "2c98d8026e1c34cb016e45ea6c064b40"

# --- Helper ---
def read_md(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

def md_block_to_xhtml(md_text):
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

def uiext_xhtml(uiext_data):
    """Создаёт описание UI расширения из JSON."""
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
        html_content = tabs.get("html", "") or ""
        js_content = tabs.get("javascript", "") or ""
        css_content = tabs.get("css", "") or ""
        if html_content:
            parts.append(f"<p><strong>HTML (длина):</strong> {len(html_content)} символов</p>")
        if js_content:
            parts.append(f"<p><strong>JavaScript (длина):</strong> {len(js_content)} символов</p>")
        if css_content:
            parts.append(f"<p><strong>CSS (длина):</strong> {len(css_content)} символов</p>")

    return "\n".join(parts)

def rule_xhtml(rid):
    """Создаёт описание одного правила автоматизации."""
    desc_path = os.path.join(DESC_DIR, f"desc_{rid}.md")
    if os.path.exists(desc_path):
        md_text = read_md(desc_path)
        if md_text:
            return md_block_to_xhtml(md_text)
    # Fallback: download from backups
    backup_path = os.path.join(BACKUPS_DIR, f"rule_{rid}.json")
    if os.path.exists(backup_path):
        with open(backup_path, encoding="utf-8") as f:
            rule = json.load(f)
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

# --- Read template ---
with open(TEMPLATE_FILE, encoding="utf-8") as f:
    body = f.read()

# --- Build automation rules for request template ---
# Template 56707 has NO automation rules at the template level
# All rules are on task templates inside the workflow

# --- Build workflow task templates sections ---
# We need to generate sections 9.2 for each task template
task_template_sections = []
tasks = wf.get("task_templates", []) if wf else []
for task in tasks:
    tid = task.get("id")
    tsubject = task.get("subject", "Задача " + str(tid))
    tphase = task.get("phase", "")
    tcategory = task.get("category", "")
    tteam = (task.get("team") or {}).get("name", "")

    section = f"<h2 id=\"DIT4ME-Задача{tid}\"><span class=\"numhead-number\">9.2.</span> {tphase}: {html_mod.escape(tsubject)}</h2>"

    # Task UI extension
    tuix = task.get("ui_extension")
    if tuix and not tuix.get("error"):
        uiext_html = f"<h3 id=\"DIT4ME-UI{tid}\"><span class=\"numhead-number\">9.2.1.</span> Требования к Расширению UI</h3>\n"
        uiext_html += uiext_xhtml(tuix)
        section += uiext_html
    else:
        section += f"<h3 id=\"DIT4ME-UI{tid}\"><span class=\"numhead-number\">9.2.1.</span> Требования к Расширению UI</h3>\n<p>Отсутствует</p>"

    # Task automation rules
    trules = task.get("automation_rules", [])
    section += f"<h3 id=\"DIT4ME-AR{tid}\"><span class=\"numhead-number\">9.2.2.</span> Требования к правилам автоматизации</h3>\n"
    if trules:
        section += f"<p>На задаче {tid} ({html_mod.escape(tsubject)}) определено {len(trules)} правил автоматизации:</p>\n<ul>\n"
        for rule in trules:
            rid = rule.get("id")
            rname = rule.get("name", "правило " + str(rid))
            link = f"https://itsm.itsm-qa.mos.ru/automation_rules/{rid}"
            section += f"<li><a href=\"{link}\">{html_mod.escape(rname)}</a> (ID {rid})</li>\n"
        section += "</ul>\n"
        # Full descriptions
        for rule in trules:
            rid = rule.get("id")
            section += f"<h3 id=\"DIT4ME-ARDesc{rid}\"><span class=\"numhead-number\">9.2.2.</span> Правило {rid}: {html_mod.escape(rule.get('name', str(rid)))}</h3>\n"
            section += rule_xhtml(rid)
    else:
        section += "<p>Правила автоматизации отсутствуют</p>"

    task_template_sections.append(section)

task_template_html = "\n\n".join(task_template_sections)

# --- Build WF UI extension ---
wf_uiext = None
# Workflow template itself doesn't have a direct UI extension in this case
# But check if there's one
wf_uiext_html = "<p>Отсутствует</p>"

# --- Build WF automation rules ---
# Template 56707 has NO direct workflow automation rules (all are on tasks)
wf_ar_html = "<p>На уровне шаблона рабочего процесса правила автоматизации отсутствуют. Правила определены на задачах внутри РП (см. раздел 9.2).</p>"

# --- Replace placeholders in template ---
# 1. History section - req_uri, req_created_at, author
body = re.sub(
    r'\*\*req_uri\*\*',
    f"https://itsm.itsm-qa.mos.ru/request_templates/{TEMPLATE_ID}",
    body
)
body = re.sub(
    r'\*\*req_created_at\*\*',
    now_str,
    body
)
# Author placeholder
body = re.sub(
    r'<p>\*\*\s*\*\*</p>',
    '<p><em>ИИ-агент ZCode</em></p>',
    body
)

# 2. req_subject
body = re.sub(
    r'<p>\*\*req_subject\*\*</p>',
    f"<p>{html_mod.escape(template_subject)}</p>",
    body
)

# 3. req_uri in table
body = re.sub(
    r'<p>\*\*req_uri\*\*</p>',
    f"<p>https://itsm.itsm-qa.mos.ru/request_templates/{TEMPLATE_ID}</p>",
    body
)

# 4. req_template_account
body = re.sub(
    r'\*\*req_template_account\*\*',
    "Каталог услуг Правительства Москвы (itsm)",
    body
)

# 5. req_template_subj
body = re.sub(
    r'\*\*req_template_subj\*\*',
    html_mod.escape(template_subject),
    body
)

# 6. req_template_category
body = re.sub(
    r'\*\*req_template_category\*\*',
    html_mod.escape(template_category),
    body
)

# 7. req_template_ui_extension_link
uiext_link_text = f"ui_extension/{template_uiext_id} — {html_mod.escape(template_uiext_name or str(template_uiext_id))}" if template_uiext_id else "Отсутствует"
body = re.sub(
    r'\*\*req_template_ui_extension_link\*\*',
    f"<p>{html_mod.escape(uiext_link_text)}</p>",
    body
)

# 8. req_ar_link — rules at template level (none for 56707)
body = re.sub(
    r'\*\*req_ar_link\*\*',
    "<p>На уровне шаблона запроса правила автоматизации отсутствуют</p>",
    body
)

# 9. req_ui_ext_ai_desc — not in this template variant, skip

# 10. req_template_ar_description — not in this template variant, skip

# 11. wf_ui_ext_desc placeholder
body = re.sub(
    r'<input[^>]*name="variableValues\.wf_ui_ext_desc"[^>]*/?>[^<]*</span>',
    f"<p>{wf_uiext_html}</p>",
    body
)

# 12. wf_ar_desc placeholder
body = re.sub(
    r'<input[^>]*name="variableValues\.wf_ar_desc"[^>]*/?>[^<]*</span>',
    f"<p>{wf_ar_html}</p>",
    body
)

# 13. task_template_name placeholder
body = re.sub(
    r'<input[^>]*name="variableValues\.task_template_name"[^>]*/?>[^<]*</span>',
    f"Список всех {len(tasks)} задач РП (см. разделы 9.2.x ниже)",
    body
)

# --- Add task template sections after the main WF section ---
# Find the end of section 9 (Шаблон Рабочего процесса) and insert task sections
# The template ends with section 9.2.2 at line 99
# We need to insert our task details after the placeholder 9.2.2

# Insert task_template_html before the </div> at the end of section 9
# Find the last section 9.2.2 placeholder and add content after it
insert_pos = body.rfind("<h3")
if insert_pos > 0:
    # Find the end of that h3 line's paragraph
    end_tag = body.find("</div>", insert_pos)
    if end_tag > 0:
        body = body[:end_tag] + task_template_html + "\n" + body[end_tag:]

# --- Add UI extension details in section 8.1.1 ---
# Replace req_template_ui_extension_description placeholder
uiext_body = structure.get("ui_extension", {})
uiext_desc = uiext_xhtml(uiext_body) if uiext_body and not uiext_body.get("error") else "<p>Отсутствует</p>"
body = re.sub(
    r'\*\*req_template_ui_extension_description\*\*',
    uiext_desc,
    body
)

# --- Fix author ---
author_macro = '<ac:structured-macro ac:name="profile"><ac:parameter ac:name="user"><ri:user ri:userkey="' + userkey + '" /></ac:parameter></ac:parameter>'
body = re.sub(
    r'(<td class="highlight-#f4f5f7 confluenceTd"[^>]*><strong[^>]*>Автор</strong>[^<]*<p><span[^>]*><span><em><span[^>]*><img[^>]*/></span></em></span></span></p></td>)',
    '<td class="highlight-#f4f5f7 confluenceTd"><p>' + author_macro + '</p></td>',
    body, count=1
)

# --- Fix enableNumbering in headings ---
body = re.sub(
    r'<h1[^>]*id="[^"]*"[^>]*><span[^>]*>\{&quot;enableNumbering&quot;:true\}</span>\</h1>',
    '<h1><span class="numhead-number">2. </span>Определения и сокращения</h1>',
    body, count=1
)
body = re.sub(
    r'<li><a href="[^"]*enableNumbering[^"]*">\{&quot;enableNumbering&quot;:true\}</a></li>',
    '<li><a href="#Определенияисокращения">2. Определения и сокращения</a></li>',
    body, count=1
)

# --- Fix TOC links ---
body = re.sub(
    r"href='#TemplatePreview-\{&quot;enableNumbering&quot;:true\}'",
    "href='#Определенияисокращения'",
    body
)

# --- Fix img tags ---
body = re.sub(r'<img([^>]*)>', lambda m: '<img' + m.group(1).rstrip() + '/>', body)

# --- Build final page ---
page_title = f"Требования к шаблону запроса {TEMPLATE_ID} — {template_subject}"

payload = {
    "type": "page",
    "title": page_title,
    "space": {"key": space_key},
    "body": {"storage": {"value": body, "representation": "storage"}},
}

# Save the built body for debugging
output_file = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\page_body_56707.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(body)
print(f"Page body saved: {output_file} ({len(body)} chars)")

# --- Publish ---
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
    print(e.read().decode("utf-8"))
except Exception as e:
    print(f"Error: {e}")
