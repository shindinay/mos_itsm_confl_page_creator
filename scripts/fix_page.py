#!/usr/bin/env python3
"""Исправление страницы Confluence 735538925 — финальная версия."""
import json
import re
import os
import html

ENV_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
desc_dir = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\artifact"
uiext_2510_path = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_UI-extension_creator\artifact\desc_2510.md"
uiext_2971_path = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_UI-extension_creator\artifact\desc_2971.md"
PAGE_ID = "735538925"

env = json.load(open(ENV_FILE, encoding="utf-8-sig"))
base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]

import urllib.request
import urllib.error

# --- GET current page ---
req = urllib.request.Request(
    base + "/rest/api/content/" + PAGE_ID + "?expand=body.storage,version",
    headers={"Authorization": "Bearer " + token}
)
resp = urllib.request.urlopen(req, timeout=15)
page_data = json.loads(resp.read().decode("utf-8"))
body = page_data["body"]["storage"]["value"]
ver = page_data["version"]["number"]
print("Current version:", ver)

# --- Read desc files with preprocessing ---
def read_md(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

def preprocess_md(text):
    text = re.sub(r'<c #([0-9a-fA-F]{6})>', r'<span style="color:#\1">', text)
    text = re.sub(r'</c>', '</span>', text)
    return text

uiext_2510_md = preprocess_md(read_md(uiext_2510_path))
uiext_2971_md = preprocess_md(read_md(uiext_2971_path))

# --- md_to_table_xhtml ---
def md_to_table_xhtml(md_text):
    lines = md_text.split("\n")
    result = []
    in_table = False
    table_lines = []
    para_lines = []

    for line in lines:
        stripped = line.strip()
        if '<table>' in line or '<table ' in line:
            if para_lines:
                text = safe_escape(" ".join(para_lines))
                result.append("<p>" + text + "</p>")
                para_lines = []
            in_table = True
            table_lines = []
        if in_table:
            table_lines.append(line)
            if '</table>' in line:
                in_table = False
                result.append("".join(table_lines))
                table_lines = []
            continue
        if stripped.startswith("### "):
            if para_lines:
                result.append("<p>" + safe_escape(" ".join(para_lines)) + "</p>")
                para_lines = []
            result.append("<h4>" + html.escape(stripped[4:]) + "</h4>")
        elif stripped.startswith("## "):
            if para_lines:
                result.append("<p>" + safe_escape(" ".join(para_lines)) + "</p>")
                para_lines = []
            result.append("<h5>" + html.escape(stripped[3:]) + "</h5>")
        elif stripped.startswith("# "):
            if para_lines:
                result.append("<p>" + safe_escape(" ".join(para_lines)) + "</p>")
                para_lines = []
            result.append("<h6>" + html.escape(stripped[2:]) + "</h6>")
        elif stripped == "":
            if para_lines:
                result.append("<p>" + safe_escape(" ".join(para_lines)) + "</p>")
                para_lines = []
        else:
            para_lines.append(stripped)
    if para_lines:
        result.append("<p>" + safe_escape(" ".join(para_lines)) + "</p>")
    return "\n".join(result)

def safe_escape(text):
    # Protect <span ...>, <strong>, <em>, <code> tags
    tag_pattern = r'<(span|strong|em|code|u)[^>]*>.*?</\1>'
    replacements = {}
    counter = [0]
    def save_tag(match):
        key = "____TAG_" + str(counter[0]) + "____"
        replacements[key] = match.group(0)
        counter[0] += 1
        return key
    text = re.sub(tag_pattern, save_tag, text, flags=re.DOTALL)
    text = html.escape(text)
    for key, tag in replacements.items():
        text = text.replace(html.escape(key), tag)
    return text

# Build section contents
uiext_2510_html = md_to_table_xhtml(uiext_2510_md)
uiext_2971_html = md_to_table_xhtml(uiext_2971_md)

# Rule data
rule_ids_template = [16207515, 16207516, 16207517, 16207518, 16207519, 16207520, 16207521, 16207522, 16207523, 16207524, 16207525, 16207526, 16207527]
rule_ids_task = [1850442, 1850446, 1850460, 1896651, 1912401, 1912403, 2030311, 2030313, 12016323, 1850444, 1982929, 6514839, 2042983, 1849706, 2627475, 2964598, 2964596, 12013871, 12013875, 12013879, 12013883]

backups_dir = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_automation_rule_descriptor\backups"
rule_names = {}
rule_triggers = {}
for rid in rule_ids_template + rule_ids_task:
    bp = os.path.join(backups_dir, "rule_" + str(rid) + ".json")
    if os.path.exists(bp):
        with open(bp, encoding="utf-8") as f:
            rd = json.load(f)
            rule_names[rid] = rd.get("name", "")
            rule_triggers[rid] = rd.get("trigger", "")

def get_rule_short_desc(rid):
    desc_path = os.path.join(desc_dir, "desc_" + str(rid) + ".md")
    if not os.path.exists(desc_path):
        return "описание отсутствует"
    with open(desc_path, encoding="utf-8") as f:
        text = f.read()
    match = re.search(r'\*\*Описание\*\*\s*\n\s*\n?(.+?)(?=\n\n|\*\*История)', text, re.DOTALL)
    if match:
        s = match.group(1).strip().replace("\n", " ")
        s = re.sub(r'action\d+:.*?\+ ', '', s)
        s = re.sub(r'action\d+:.*?\+', '', s)
        if len(s) > 200:
            s = s[:200]
        return s
    return "описание отсутствует"

trigger_map = {
    "on status update": "при изменении статуса",
    "on create": "при создании",
    "after delay": "после задержки",
    "on custom_fields update": "при обновлении custom_fields",
}

def rule_row(rid, name, trigger, summary, seq):
    t = trigger_map.get(trigger, trigger)
    link = "https://itsm.itsm-qa.mos.ru/automation_rules/" + str(rid)
    en = html.escape(name)
    es = html.escape(summary)
    return (
        '<tr><td style="text-align:left">' + str(seq) + '</td>'
        '<td style="text-align:left">' + str(rid) + '</td>'
        '<td style="text-align:left">' + en + '</td>'
        '<td style="text-align:left">' + t + '</td>'
        '<td style="text-align:left">' + es + '</td>'
        '<td style="text-align:left"><ac:link><ri:url ri:value="' + link + '"/></ac:link></td>'
        '</tr>'
    )

# 8.1.2
ar_812_html = '<p>13 правил автоматизации на шаблоне запроса:</p><table><tr>'
ar_812_html += '<th style="text-align:left;background-color:rgb(221, 221, 221)">№</th>'
ar_812_html += '<th style="text-align:left;background-color:rgb(221, 221, 221)">ID</th>'
ar_812_html += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Название</th>'
ar_812_html += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Триггер</th>'
ar_812_html += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Суть</th>'
ar_812_html += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Карточка</th></tr>'
for i, rid in enumerate(rule_ids_template, 1):
    name = rule_names.get(rid, "правило " + str(rid))
    trigger = rule_triggers.get(rid, "")
    summary = get_rule_short_desc(rid)
    ar_812_html += rule_row(rid, name, trigger, summary, i)
ar_812_html += '</table>'

wf_ui_ext = '<p>Отсутствует (у РП 16919 нет своего UI-расширения)</p>'
wf_ar = '<p>Отсутствуют (у РП 16919 нет правил автоматизации)</p>'

# 8.3.2
task_groups = [
    (3698, [1850442, 1850446, 1850460, 1896651, 1912401, 1912403, 2030311, 2030313, 12016323, 1850444, 1982929, 6514839, 2042983, 1849706]),
    (7337, [2627475, 2964598, 2964596]),
    (29151, [12013871, 12013875, 12013879, 12013883]),
]
task_titles = {
    3698: "Согласование с владельцем/представителем пространства. Предоставление/отзыв лицензии для работников",
    7337: "Авто подготовка РП (для сгенерированного запроса)",
    29151: "Авто подготовка РП. Предоставление/отзыв лицензии для работников",
}

ar_832_parts = []
for tid, rules in task_groups:
    ar_832_parts.append('<h5>Задача ' + str(tid) + ' — ' + task_titles[tid] + ' (' + str(len(rules)) + ' правил):</h5><table><tr>')
    ar_832_parts.append('<th style="text-align:left;background-color:rgb(221, 221, 221)">№</th>')
    ar_832_parts.append('<th style="text-align:left;background-color:rgb(221, 221, 221)">ID</th>')
    ar_832_parts.append('<th style="text-align:left;background-color:rgb(221, 221, 221)">Название</th>')
    ar_832_parts.append('<th style="text-align:left;background-color:rgb(221, 221, 221)">Триггер</th>')
    ar_832_parts.append('<th style="text-align:left;background-color:rgb(221, 221, 221)">Суть</th>')
    ar_832_parts.append('<th style="text-align:left;background-color:rgb(221, 221, 221)">Карточка</th></tr>')
    for i, rid in enumerate(rules, 1):
        name = rule_names.get(rid, "правило " + str(rid))
        trigger = rule_triggers.get(rid, "")
        summary = get_rule_short_desc(rid)
        ar_832_parts.append(rule_row(rid, name, trigger, summary, i))
    ar_832_parts.append('</table>')
ar_832_html = '<p>Сводка по 21 правилу задач (3698: 14; 7337: 3; 29151: 4):</p>' + "".join(ar_832_parts)

req_first_comment = '<p>\\- (заполняется при создании конкретного запроса)</p>'

# --- STEP 1: Replace span placeholders ---
def replace_span(body, var_name, content):
    pattern = r'<span class="templateparameter">\(' + var_name + r'\)</span>'
    count = len(re.findall(pattern, body))
    if count > 0:
        body = re.sub(pattern, content, body, count=1)
        print("  Replaced span: " + var_name + " (" + str(count) + ")")
    return body

body = replace_span(body, "req_subject", html.escape("mock - МосИТСМ. Предоставление/отзыв лицензии для работников"))
body = replace_span(body, "req_template_subj", html.escape("mock - МосИТСМ. Предоставление/отзыв лицензии для работников"))
body = replace_span(body, "task_template_name", html.escape("3698: Согласование с владельцем/представителем пространства. Предоставление/отзыв лицензии для работников; 7337: Авто подготовка РП; 29151: Авто подготовка РП. Предоставление/отзыв лицензии"))
body = replace_span(body, "req_first_comment", req_first_comment)
body = replace_span(body, "req_ui_ext_ai_desc", uiext_2510_html)
body = replace_span(body, "req_template_automation_rule_ai_description", ar_812_html)
body = replace_span(body, "wf_ui_ext_desc", wf_ui_ext)
body = replace_span(body, "wf_ar_desc", wf_ar)

# --- STEP 2: Replace ac:image / ac:link blocks for req_uri and req_template_account ---
# Pattern: <ac:link>...<ri:url ri:value="...template-variable?name=req_uri"/>...</ac:link></span>
def replace_ac_image(body, var_name, replacement):
    # Match the entire block from <ac:link> (or <ac:link><ac:link ...>) to </span>
    pattern = r'<ac:link>[^<]*<ac:link[^>]*>.*?<ri:url[^>]*ri:value="[^"]*template-variable\?' + var_name + '"[^>]*/>.*?</ac:link></ac:link></span>'
    if re.search(pattern, body, re.DOTALL):
        body = re.sub(pattern, replacement, body, count=1, flags=re.DOTALL)
        print("  Replaced ac:link: " + var_name)
        return body
    # Try simpler pattern: just the ri:value part inside ac:link
    pattern2 = r'<ri:url[^>]*ri:value="[^"]*template-variable\?' + var_name + '"[^>]*/>'
    if re.search(pattern2, body):
        body = re.sub(pattern2, '<ri:url ri:value="' + replacement + '"/></ri:url>', body, count=1)
        print("  Replaced ri:url: " + var_name)
        return body
    # Check what's actually there
    idx = body.find(var_name)
    if idx >= 0:
        print("  CANNOT REPLACE " + var_name + " at pos " + str(idx))
        print("  Context:", repr(body[max(0,idx-50):idx+100]))
    return body

body = replace_ac_image(body, "req_uri", "https://itsm.itsm-qa.mos.ru/request_templates/73558")
body = replace_ac_image(body, "req_template_account", "Каталог услуг Правительства Москвы (itsm)")

# --- STEP 3: Replace 8.3.1 heading with content AFTER it ---
# The pattern is: <h3>...8.3.1...</h3> followed immediately by another <h3> (8.3.2)
# We need to insert content after the 8.3.1 h3
idx_831 = body.find('8.3.1.')
if idx_831 >= 0:
    # Find the closing </h3> of the 8.3.1 heading
    h3_close = body.find('</h3>', idx_831)
    if h3_close >= 0:
        body = body[:h3_close+5] + '\n' + uiext_2971_html + body[h3_close+5:]
        print("  Inserted 8.3.1 content after h3")
    else:
        print("  8.3.1: could not find </h3>")
else:
    print("  8.3.1: heading not found")

# 8.3.2 - same approach
idx_832 = body.find('8.3.2.')
if idx_832 >= 0:
    h3_close = body.find('</h3>', idx_832)
    if h3_close >= 0:
        body = body[:h3_close+5] + '\n' + ar_832_html + body[h3_close+5:]
        print("  Inserted 8.3.2 content after h3")
    else:
        print("  8.3.2: could not find </h3>")
else:
    print("  8.3.2: heading not found")

# --- STEP 4: Fill table 8.1 rows ---
body = re.sub(
    r'(<td class="confluenceTd"><p>Название шаблона</p></td><td class="confluenceTd"><p><br/></p></td>)',
    '<td class="confluenceTd"><p>Название шаблона</p></td><td class="confluenceTd"><p>mock - МосИТСМ. Предоставление/отзыв лицензии для работников</p></td>',
    body, count=1
)
body = re.sub(
    r'(<td class="confluenceTd"><p>Категория</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Категория</p></td><td class="confluenceTd"><p>rfc</p></td>',
    body, count=1
)
body = re.sub(
    r'(<td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><br/></td>)',
    '<td class="confluenceTd"><p>Расширение UI</p></td><td class="confluenceTd"><p>2510: Предоставление прав доступа в 4me для работников</p></td>',
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

# --- STEP 5: Fix heading duplicate ---
body = re.sub(
    r'<h1[^>]*id="[^"]*"[^>]*><span[^>]*>2\. </span>\{[^}]*enableNumbering[^}]*\}</h1>',
    '<h1><span class="numhead-number">2. </span>Общие сведения</h1>',
    body, count=1
)

# --- STEP 6: Fix unescaped & ---
# Replace bare & with &amp; - but not inside <table>, <tr>, <th>, <td>, <span style, <ac:
# Strategy: walk through text and escape & not followed by valid entity chars
def fix_unescaped_ampersands(text):
    # This is a targeted fix: find & that are inside <p> tags and are not entities
    # First, process paragraph by paragraph
    def replace_in_p(match):
        p_content = match.group(1)
        # Replace bare & with &amp;
        p_content = re.sub(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', r'&amp;', p_content)
        return '<p>' + p_content + '</p>'
    
    # Process <p>...</p> blocks
    text = re.sub(r'<p>(.*?)</p>', replace_in_p, text, flags=re.DOTALL)
    
    # Also fix any bare & outside <p> tags (like in table content, span text)
    # For table cells <td>...</td>
    def replace_in_td(match):
        td_content = match.group(1)
        td_content = re.sub(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', r'&amp;', td_content)
        return '<td>' + td_content + '</td>'
    text = re.sub(r'<td[^>]*>(.*?)</td>', replace_in_td, text, flags=re.DOTALL)
    
    # For <th>...</th>
    def replace_in_th(match):
        th_content = match.group(1)
        th_content = re.sub(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', r'&amp;', th_content)
        return '<th>' + th_content + '</th>'
    text = re.sub(r'<th[^>]*>(.*?)</th>', replace_in_th, text, flags=re.DOTALL)
    
    # For <span ...>...</span>
    def replace_in_span(match):
        full = match.group(0)
        # Extract style and content
        style_match = re.match(r'(<span[^>]*>)(.*?)(</span>)', full, re.DOTALL)
        if style_match:
            tag = style_match.group(1)
            content = style_match.group(2)
            content = re.sub(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', r'&amp;', content)
            return tag + content + '</span>'
        return full
    text = re.sub(r'<span[^>]*>.*?</span>', replace_in_span, text, flags=re.DOTALL)
    
    # For text between </p> and next < or end
    # This catches bare text between block elements
    def replace_bare_text(match):
        text_part = match.group(0)
        text_part = re.sub(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', r'&amp;', text_part)
        return text_part
    # Text between closing tags
    text = re.sub(r'</p>(.+?)<h[1-6]', replace_bare_text, text)
    
    return text

body = fix_unescaped_ampersands(body)

# --- Verify XHTML before PUT ---
# Check for <c # tags
if re.search(r'<c #[0-9a-fA-F]{6}>', body):
    print("  WARNING: <c #> tags still present!")
else:
    print("  OK: no <c #> tags")

# Check unescaped &
amp_issues = re.findall(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', body)
print("  Unescaped & count:", len(amp_issues))

# Check required content
for var in ['req_ui_ext_ai_desc', 'req_template_automation_rule_ai_description', 'wf_ui_ext_desc', 'wf_ar_desc', 'task_template_name', 'req_template_subj']:
    if '<span class="templateparameter">(' + var + ')</span>' in body:
        print("  STILL PRESENT: " + var)
    else:
        print("  OK: " + var)

# Check 8.3.1 and 8.3.2
if '8.3.1' in body:
    idx = body.find('8.3.1')
    after = body[idx:idx+200]
    if 'Предоставление' in after and '2971' in after[:200]:
        print("  8.3.1: has content")
    else:
        print("  8.3.1: content check:", repr(after[:150]))

if '8.3.2' in body:
    idx = body.find('8.3.2')
    after = body[idx:idx+200]
    if 'Сводка' in after:
        print("  8.3.2: has content")
    else:
        print("  8.3.2: content check:", repr(after[:150]))

# Table 8.1 checks
for t in ['mock - МосИТСМ. Предоставление/отзыв лицензии для работников', 'rfc', '2510:', '13 правил', '16919:']:
    if t in body:
        print("  Table 8.1: " + t + " OK")
    else:
        print("  Table 8.1: " + t + " MISSING")

# req_uri and req_template_account checks
if 'itsm-qa.mos.ru/request_templates/73558' in body:
    print("  req_uri: replaced with URL")
else:
    print("  req_uri: MISSING")
if 'Каталог услуг Правительства Москвы' in body:
    print("  req_template_account: replaced")
else:
    print("  req_template_account: MISSING")

print("\nBody length:", len(body))

# --- PUT ---
new_ver = ver + 1
put_data = {
    "id": PAGE_ID,
    "type": "page",
    "title": page_data["title"],
    "version": {"number": new_ver, "minorEdit": False},
    "body": {"storage": {"value": body, "representation": "storage"}},
}

req_put = urllib.request.Request(
    base + "/rest/api/content/" + PAGE_ID,
    data=json.dumps(put_data).encode("utf-8"),
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    },
    method="PUT"
)

try:
    resp_put = urllib.request.urlopen(req_put, timeout=30)
    result = json.loads(resp_put.read().decode("utf-8"))
    print("\nPUT SUCCESS! New version:", result["version"]["number"])
    page_url = result["_links"]["base"] + result["_links"]["webui"]
    print("Page URL:", page_url)
except urllib.error.HTTPError as e:
    print("\nPUT ERROR: " + str(e.code))
    err = e.read().decode("utf-8")
    print(err[:2000])
    with open(r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\temp\debug_body_v5.html", "w", encoding="utf-8") as f:
        f.write(body)
    print("Body saved for debugging")
except Exception as e:
    print("\nPUT ERROR: " + str(e))
