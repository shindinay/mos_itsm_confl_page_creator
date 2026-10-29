#!/usr/bin/env python3
"""Создание страницы Confluence REQ — фикс XHTML."""
import json
import re
import os
import html

# --- Config ---
ENV_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
TEMPLATE_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\template_body.html"
PARENT_ID = "735534111"

env = json.load(open(ENV_FILE, encoding="utf-8-sig"))
base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]
space_key = "DIT4ME"
userkey = "2c98d8026e1c34cb016e45ea6c064b40"

# Paths
uiext_2510_path = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_UI-extension_creator\artifact\desc_2510.md"
uiext_2971_path = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_UI-extension_creator\artifact\desc_2971.md"
desc_dir = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\artifact"
backups_dir = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\backups"

rule_ids = [
    16207515, 16207516, 16207517, 16207518, 16207519, 16207520, 16207521,
    16207522, 16207523, 16207524, 16207525, 16207526, 16207527,
    1850442, 1850446, 1850460, 1896651, 1912401, 1912403, 2030311,
    2030313, 12016323, 1850444, 1982929, 6514839, 2042983, 1849706,
    2627475, 2964598, 2964596, 12013871, 12013875, 12013879, 12013883,
]

# Read rule names
rule_names = {}
for rid in rule_ids:
    backup_path = os.path.join(backups_dir, "rule_" + str(rid) + ".json")
    if os.path.exists(backup_path):
        with open(backup_path, encoding="utf-8") as f:
            rdata = json.load(f)
            rule_names[rid] = rdata.get("name", "rule_" + str(rid))

def read_md(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return "(файл не найден)"

def md_block_to_xhtml(md_text):
    lines = md_text.split("\n")
    blocks = []
    current_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            blocks.append('<h4>' + html.escape(stripped[2:]) + '</h4>')
        elif stripped.startswith("## "):
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            blocks.append('<h5>' + html.escape(stripped[3:]) + '</h5>')
        elif stripped.startswith("### "):
            if current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            blocks.append('<h6>' + html.escape(stripped[4:]) + '</h6>')
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
            if '<table' in text or '<strong>' in text or '<em>' in text:
                result.append('<p>' + text + '</p>')
            else:
                result.append('<p>' + html.escape(text) + '</p>')
    
    return "\n".join(result)

# --- Build content ---
uiext_2510_md = read_md(uiext_2510_path)
uiext_2971_md = read_md(uiext_2971_path)
req_ui_ext_ai_desc = md_block_to_xhtml(uiext_2510_md)
uiext_2971_html = md_block_to_xhtml(uiext_2971_md)

# Template rules list for 8.1.2
template_rule_names = [
    "16207515: Закрыть запрос при завершении РП",
    "16207516: Отправка писем",
    "16207517: Проброс полей в задачу #4327 (отключено)",
    "16207518: тест подмены пространства (отключено)",
    "16207519: Закрыть запрос если переоткрыли",
    "16207520: Проброс полей в задачи",
    "16207521: Запуск проброса полей",
    "16207522: Обработка сгенерированного запроса",
    "16207523: Обработка сгенерированного запроса: Отмена утверждения представителей",
    "16207524: Обработка сгенерированного запроса: Отмена пакет Внутренний",
    "16207525: Обработка сгенерированного запроса: Закрытие задачи на Авто подготовку",
    "16207526: Завершено = Проброс коммента в задачу",
    "16207527: Смена команды, если участник - Служебная УЗ",
]

ar_list_parts = []
for rname in template_rule_names:
    ar_list_parts.append('<li>' + html.escape(rname) + '</li>')
req_ar_desc_template = '<p>13 правил автоматизации на шаблоне:</p>' + ''.join(ar_list_parts)

wf_ui_ext_desc = '<p>Отсутствует</p>'
wf_ar_desc = '<p>Отсутствуют</p>'

task_names_map = {
    3698: "Согласование с владельцем/представителем пространства. Предоставление/отзыв лицензии для работников",
    7337: "Авто подготовка РП (для сгенерированного запроса)",
    29151: "Авто подготовка РП. Предоставление/отзыв лицензии для работников",
}
task_template_name = "3698: " + task_names_map[3698] + "; 7337: " + task_names_map[7337] + "; 29151: " + task_names_map[29151]

# Task rules summary for 8.3.2
task_3698_rules = [1850442, 1850446, 1850460, 1896651, 1912401, 1912403, 2030311, 2030313, 12016323, 1850444, 1982929, 6514839, 2042983, 1849706]
task_7337_rules = [2627475, 2964598, 2964596]
task_29151_rules = [12013871, 12013875, 12013879, 12013883]

task_summary_parts = []
for tid, rules in [(3698, task_3698_rules), (7337, task_7337_rules), (29151, task_29151_rules)]:
    task_summary_parts.append('<p><strong>Задача ' + str(tid) + ' — ' + task_names_map[tid] + ' (' + str(len(rules)) + ' правил):</strong></p>')
    for rid in rules:
        name = rule_names.get(rid, "правило " + str(rid))
        desc_path = os.path.join(desc_dir, "desc_" + str(rid) + ".md")
        if os.path.exists(desc_path):
            with open(desc_path, encoding="utf-8") as f:
                desc_text = f.read()
            match = re.search(r'\*\*Описание\*\*\s*\n\s*\n?(.+?)(?=\n\n|\*\*История)', desc_text, re.DOTALL)
            if match:
                summary = match.group(1).strip().replace("\n", " ")[:300]
            else:
                summary = "описание отсутствует"
        else:
            summary = "описание не сгенерировано"
        link = "https://itsm.itsm-qa.mos.ru/automation_rules/" + str(rid)
        escaped_summary = html.escape(summary)[:300]
        task_summary_parts.append(
            '<li>ID ' + str(rid) + ': ' + html.escape(name) + ' — ' + escaped_summary + ' <a href="' + link + '">' + link + '</a></li>'
        )
task_rules_html = '<p>Сводка по 21 правилу задач:</p>' + ''.join(task_summary_parts)

# --- Read template and make img tags XHTML-compliant ---
with open(TEMPLATE_FILE, encoding="utf-8") as f:
    body = f.read()

# FIX: Make <img> tags self-closing (add trailing /)
body = re.sub(r'<img([^>]*)>', lambda m: '<img' + m.group(1).rstrip() + '/>', body)

# Replace author
author_macro = '<ac:structured-macro ac:name="profile"><ac:parameter ac:name="user"><ri:user ri:userkey="' + userkey + '" /></ac:parameter></ac:structured-macro>'
body = re.sub(
    r'(<td class="highlight-#f4f5f7 confluenceTd"[^>]*><strong[^>]*>Автор</strong>[^<]*<p><span[^>]*><span><em><span[^>]*><img[^>]*/></span></em></span></span></p></td>)',
    '<td class="highlight-#f4f5f7 confluenceTd"><p>' + author_macro + '</p></td>',
    body, count=1
)

# Fix enableNumbering in headings
body = re.sub(r'<h1[^>]*id="[^"]*"[^>]*><span[^>]*>2\. </span>\{[^}]*enableNumbering[^}]*\}</h1>', '<h1><span class="numhead-number">2. </span>Общие сведения</h1>', body, count=1)
body = re.sub(
    r'<li><a href="[^"]*enableNumbering[^"]*">2\.\s*{[^}]*enableNumbering[^}]*}</a></li>',
    '<li><a href="#Общиесведения">2. Общие сведения</a></li>',
    body, count=1
)

# Simple text replacements
simple_replacements = [
    ("req_subject", "mock - МосИТСМ. Предоставление/отзыв лицензии для работников"),
    ("req_uri", "https://itsm.itsm-qa.mos.ru/request_templates/73558"),
    ("req_template_account", "Каталог услуг Правительства Москвы (itsm)"),
    ("req_template_subj", "mock - МосИТСМ. Предоставление/отзыв лицензии для работников"),
    ("task_template_name", task_template_name),
]
for var_name, value in simple_replacements:
    pattern = r'<input[^>]*name="variableValues\.' + var_name + r'"[^>]*>[^<]*</span>'
    body = re.sub(pattern, html.escape(value), body, count=1)

# Multiline HTML replacements
replacements_html = [
    ("req_ui_ext_ai_desc", req_ui_ext_ai_desc),
    ("req_template_automation_rule_ai_description", req_ar_desc_template),
    ("wf_ui_ext_desc", wf_ui_ext_desc),
    ("wf_ar_desc", wf_ar_desc),
]
for var_name, value in replacements_html:
    pattern = r'<input[^>]*name="variableValues\.' + var_name + r'"[^>]*>[^<]*</span>'
    body = re.sub(pattern, value, body, count=1)

# Fill 8.1 table
body = re.sub(
    r'(<td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><p>2510: Предоставление прав доступа в 4me для работников (вкладка Информацию)</p></td>',
    body, count=1
)
body = re.sub(
    r'(<td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Правила автоматизации</p></td><td class="confluenceTd"><p>13 правил (см. раздел 8.1.2)</p></td>',
    body, count=1
)
body = re.sub(
    r'(<td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Шаблон рабочего процесса</p></td><td class="confluenceTd"><p>16919: mock - МосИТСМ. Предоставление/отзыв лицензии для работников</p></td>',
    body, count=1
)

# 8.3.1 - insert UI extension 2971
body = re.sub(
    r'(<h3 id="[^"]*">8\.3\.1\. </span>Требования к Расширению UI</h3>)',
    r'\1\n' + uiext_2971_html,
    body, count=1
)

# 8.3.2 - insert task rules summary
body = re.sub(
    r'(<h3 id="[^"]*">8\.3\.2\. </span><span>Требования к правилам автоматизации</span></h3>)',
    r'\1\n' + task_rules_html,
    body, count=1
)

# Write
output_file = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\page_body.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(body)

print("Page body written: " + str(len(body)) + " chars")

# Create page
payload = {
    "type": "page",
    "title": '"ФТ"_mock - МосИТСМ. Предоставление/отзыв лицензии для работников - Предоставление/отзыв лицензии для работников',
    "space": {"key": space_key},
    "body": {"storage": {"value": body, "representation": "storage"}},
    "ancestors": [{"id": PARENT_ID}]
}

with open(r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f)

import urllib.request
import urllib.error

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
    print("SUCCESS! Page ID: " + page_id)
    print("Page URL: " + page_url)
except urllib.error.HTTPError as e:
    print("HTTP Error: " + str(e.code))
    print(e.read().decode("utf-8"))
except Exception as e:
    print("Error: " + str(e))
