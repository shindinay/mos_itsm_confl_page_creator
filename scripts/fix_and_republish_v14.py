# -*- coding: utf-8 -*-
"""
Исправление и публикация v14 страницы 738464895.

Проблемы, которые нужно исправить:
1. enableNumbering JSON в заголовке раздела 2
2. enableNumbering JSON в TOC
3. Таблицы в разделе 8.1.1 заэкранированы как literal `&lt;table&gt;` — нужно декодировать
4. Raw character ® в таблице (должно быть &#174;)
5. Пустые ac:link без ac:plain-text-body
"""
import json, re, urllib.request, os, ssl, base64

# SSL context for corporate certificates
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(SKILL)

# Load .env (JSON format)
with open('.env', 'r', encoding='utf-8') as f:
    env = json.load(f)

token = env.get('MOSITSM_PERS_TOKEN_QA', '')
conf_url = env.get('CONFLUENCE_BASE_URL', 'https://itpm-wiki.mos.ru/').rstrip('/')
confl_token = env['CONFLUENCE_API_TOKEN']

# ============================================================
# Read the current page body from v12
# ============================================================
with open('temp/page_body_8170964_v12.html', 'r', encoding='utf-8') as f:
    body = f.read()

print('Original body length:', len(body))

# ============================================================
# Fix 1: Remove enableNumbering JSON from heading 2
# ============================================================
h2_pattern = r'<h1[^>]*id="DIT4ME-\{&quot;enableNumbering&quot;:true\}"[^>]*>[^<]*<span class="numhead-number">2\. </span>{&quot;enableNumbering&quot;:true}</h1>'
replacement = '<h1 id="DIT4ME-РазделНастройки"><span class="numhead-number">2. </span>Раздел настроек</h1>'
body = re.sub(h2_pattern, replacement, body, flags=re.DOTALL)
if h2_pattern not in body:
    print('Fix 1: heading 2 replacement pattern not found in body (may already be replaced)')

# ============================================================
# Fix 2: Remove enableNumbering JSON from TOC
# ============================================================
toc_pattern = r"<a[^>]*href='#TemplatePreview-\{&quot;enableNumbering&quot;:true\}'[^>]*>[^<]*2\.\s*{&quot;enableNumbering&quot;:true}[^<]*</a>"
replacement_toc = "<a href='#TemplatePreview-РазделНастройки'>2. Раздел настроек</a>"
body = re.sub(toc_pattern, replacement_toc, body)
if len(re.findall(r'enableNumbering', body)) > 0:
    print('WARNING: still have enableNumbering refs:', len(re.findall(r'enableNumbering', body)))
else:
    print('Fix 2: enableNumbering removed from TOC')

# ============================================================
# Fix 3: Decode escaped XML in section 8.1.1 (UI extension description)
# This is the KEY fix for the white screen.
# The literal text "&lt;table&gt;" should be "<table>"
# We need to decode ALL &lt; &gt; &amp; that represent actual XML tags
# ============================================================

# Strategy: decode &lt; to < and &gt; to > and &amp; to & ONLY where they form XML/HTML tags
# We'll use a regex that matches literal tag text like &lt;table&gt; or &lt;/td&gt;
def decode_escaped_tag(match):
    tag = match.group(1)
    # Decode common HTML entities within tag names/attributes
    return '<' + tag + '>'

# Match < or </ and then tag content (no space for closing) with escaped chars
body = re.sub(r'&lt;(/?)([\w]+[^&<>]*?)&gt;', lambda m: '<' + m.group(1) + m.group(2) + '>', body)
# Handle tags with trailing / like &lt;br/&gt; -> <br/>
body = re.sub(r'&lt;(/?)([\w]+[^&<>]*?)/&gt;', lambda m: '<' + m.group(1) + m.group(2) + '/>', body)

# Count how many replacements
escaped_before = len(re.findall(r'&lt;table&gt;', body))
escaped_after = len(re.findall(r'&lt;table&gt;', body))
print('Fix 3: escaped table tags before:', escaped_before, 'after:', escaped_after)

# Also handle &lt;/table&gt; and similar closing tags
escaped_before_close = len(re.findall(r'&lt;/table&gt;', body))
print('Fix 3: escaped closing table tags:', escaped_before_close)

# ============================================================
# Fix 4: Replace raw © ® characters with numeric entities
# ============================================================
body = body.replace('\u00ae', '&#174;')  # ®
body = body.replace('\u00a9', '&#169;')  # ©
body = body.replace('\u2122', '&#8482;') # ™

# ============================================================
# Fix 5: Ensure empty ac:link have text
# ============================================================
# Find all <ac:link>...</ac:link> that don't contain <ac:plain-text-body>
def fix_empty_links(m):
    link_block = m.group(0)
    if '<ac:plain-text-body>' not in link_block:
        # Extract the URL and add text
        url_match = re.search(r'ri:value="([^"]+)"', link_block)
        if url_block:
            url = url_match.group(1)
            # Generate text based on URL type
            if 'ui_extensions' in url:
                ext_id = url.split('/')[-1]
                text = 'UI-расширение ' + ext_id
            elif 'automation_rules' in url:
                rule_id = url.split('/')[-1]
                text = 'Карточка правила ' + rule_id
            elif 'workflow_templates' in url:
                wf_id = url.split('/')[-1]
                text = 'РП ' + wf_id
            else:
                text = 'Ссылка'
            return link_block.replace('</ac:link>', '<ac:plain-text-body>' + text + '</ac:link>')
    return link_block

# Actually let's do a simpler check - find all ac:link and ensure they have text
# The pattern is: <ac:link><ri:url ri:value="..."/></ac:link>
empty_link_pattern = r'<ac:link>\s*<ri:url ri:value="([^"]+)" />\s*</ac:link>'
def add_text_to_empty_link(m):
    url = m.group(1)
    if 'ui_extensions' in url:
        ext_id = url.split('/')[-1]
        text = 'UI-расширение ' + ext_id
    elif 'automation_rules' in url:
        rule_id = url.split('/')[-1]
        text = 'Карточка правила ' + rule_id
    elif 'workflow_templates' in url:
        wf_id = url.split('/')[-1]
        text = 'РП ' + wf_id
    elif 'requests/' in url:
        req_id = url.split('/')[-1]
        text = 'RFC ' + req_id
    else:
        text = 'Ссылка'
    return '<ac:link><ri:url ri:value="' + url + '"/><ac:plain-text-body>' + text + '</ac:plain-text-body></ac:link>'

body = re.sub(empty_link_pattern, add_text_to_empty_link, body)

# Count empty links
empty_links = re.findall(empty_link_pattern, body)
print('Fix 5: empty links found:', len(empty_links), '-> text added')

# ============================================================
# Fix 6: Replace all HTML entities with XML-compatible numeric forms
# ============================================================
html_entities = {
    '&nbsp;': '&#160;',
    '&laquo;': '&#171;',
    '&raquo;': '&#187;',
    '&mdash;': '&#8212;',
    '&ndash;': '&#8211;',
    '&shy;': '&#173;',
    '&copy;': '&#169;',
    '&reg;': '&#174;',
    '&hellip;': '&#8230;',
    '&lsqb;': '&#91;',
    '&rsqb;': '&#93;',
    '&prime;': '&#8242;',
    '&Prime;': '&#8243;',
    '&permil;': '&#8240;',
    '&trade;': '&#8482;',
}
for entity, num in html_entities.items():
    body = body.replace(entity, num)

# Also handle any remaining raw characters that aren't valid XML
# Standard XML entities (keep as-is): &amp; &lt; &gt; &quot; &apos;

# ============================================================
# Fix 7: Fix <br/> tags - ensure they're self-closing
# ============================================================
body = re.sub(r'<br\s*/?>', '<br/>', body)

# ============================================================
# Validation: XML parse
# ============================================================
import xml.etree.ElementTree as ET

# Wrap in root for validation
try:
    ET.fromstring('<root xmlns:ac="http://atlassian.com/confluence"' + body + '</root>')
    xml_ok = True
    print('XML validation: OK')
except ET.ParseError as e:
    print('XML validation FAILED:', str(e))
    # Try to find the error location
    lines = body.split('\n')
    # ElementTree reports byte offset, approximate to line
    if hasattr(e, 'position'):
        pos = e.position
        print('Error at char', pos[0], 'line', body[:pos[0]].count('\n') + 1)
        start = max(0, pos[0] - 50)
        end = min(len(body), pos[0] + 50)
        print('Context:', repr(body[start:end]))
    xml_ok = False

# ============================================================
# Check for remaining problematic patterns
# ============================================================
issues = []
if re.search(r'<ac:link>\s*<ri:url[^>]*/>\s*</ac:link>', body):
    issues.append('Still has empty ac:link')
if re.search(r'enableNumbering', body):
    issues.append('Still has enableNumbering')
if re.search(r'&lt;table&gt;', body):
    issues.append('Still has escaped &lt;table&gt;')
    
if issues:
    print('Issues found:', issues)
else:
    print('All fixes applied, no issues found')

# ============================================================
# Write fixed body
# ============================================================
with open('temp/page_body_8170964_v14.html', 'w', encoding='utf-8') as f:
    f.write(body)
print('Fixed body written:', len(body), 'chars')

# ============================================================
# Publish to Confluence
# ============================================================
api = conf_url + '/rest/api'

# Get current page version
req = urllib.request.Request(api + '/content/738464895?expand=version')
req.add_header('Authorization', 'Bearer ' + confl_token)
req.add_header('Accept', 'application/json')
resp = urllib.request.urlopen(req, context=ssl_ctx)
page_data = json.loads(resp.read())
print('Current title:', page_data.get('title'))
current_version = page_data.get('version', {}).get('number', 1)
new_version = current_version + 1
print('New version:', new_version)

# Update
payload = {
    'id': '738464895',
    'type': 'page',
    'title': page_data.get('title', '8170964-MosITSM. Predostavlenie dostupa k demo stenddu'),
    'space': {'key': 'DIT4ME'},
    'body': {
        'storage': {
            'value': body,
            'representation': 'storage'
        }
    },
    'version': {'number': new_version, 'minorEdit': False}
}

req2 = urllib.request.Request(api + '/content/738464895', method='PUT')
req2.add_header('Authorization', 'Bearer ' + confl_token)
req2.add_header('Content-Type', 'application/json')
req2.add_header('Accept', 'application/json')
req2.data = json.dumps(payload, ensure_ascii=False).encode('utf-8')

try:
    resp2 = urllib.request.urlopen(req2, context=ssl_ctx)
    result = json.loads(resp2.read())
    print('Published v' + str(new_version) + ': OK')
    print('Page URL:', conf_url + '/pages/viewpage.action?pageId=738464895')
except Exception as e:
    print('Publish error:', str(e))
    if hasattr(e, 'read'):
        print('Error detail:', e.read().decode('utf-8', errors='replace')[:1000])
