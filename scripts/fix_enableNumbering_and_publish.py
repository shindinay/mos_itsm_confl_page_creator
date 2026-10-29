# -*- coding: utf-8 -*-
"""Исправление заголовка раздела 2 и публикация v13."""
import json, re, urllib.request, os, ssl, base64

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(SKILL)

# Read v12 fixed body
with open('temp/page_body_8170964_v12_fixed.html', 'r', encoding='utf-8') as f:
    body = f.read()

# Fix 1: replace broken heading 2 (h1 with enableNumbering JSON)
h1_pattern = r'<h1[^>]*id="DIT4ME-\{&quot;enableNumbering&quot;:true\}"[^>]*>.*?<span class="numhead-number">2\. </span>{&quot;enableNumbering&quot;:true}</h1>'
body = re.sub(h1_pattern,
              '<h1 id="DIT4ME-РазделНастройки"><span class="numhead-number">2. </span>Раздел настроек</h1>',
              body, flags=re.DOTALL)

# Fix 2: replace broken TOC anchor for section 2
toc_pattern = r"<a href='#TemplatePreview-\{&quot;enableNumbering&quot;:true\}'>2\.\s*{&quot;enableNumbering&quot;:true}</a>"
body = re.sub(toc_pattern,
              "<a href='#TemplatePreview-РазделНастройки'>2. Раздел настроек</a>",
              body)

# Verify
rem = len(re.findall(r'enableNumbering', body))
print('Remaining enableNumbering refs:', rem)

# Fix 3: ensure ® is numeric entity
body = body.replace('\u00ae', '&#174;')

# Fix 4: other raw HTML entities
for entity, num in [('&#160;', '&#160;'), ('&laquo;', '&#171;'), ('&raquo;', '&#187;'),
                    ('&mdash;', '&#8212;'), ('&ndash;', '&#8211;'), ('&copy;', '&#169;'),
                    ('&rsquo;', '&#8217;'), ('&lsquo;', '&#8216;')]:
    if entity.startswith('&') and not entity.startswith('&#'):
        body = body.replace(entity, num)

# Write final body
with open('temp/page_body_8170964_v13.html', 'w', encoding='utf-8') as f:
    f.write(body)
print('Fixed body length:', len(body))

# Load token (JSON format .env)
token = ''
with open('.env', 'r', encoding='utf-8') as ef:
    env_data = json.load(ef)
    token = env_data.get('MOSITSM_PERS_TOKEN_QA', '')
if not token:
    print('ERROR: no token found')
    exit(1)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# Load Confluence config
with open('.env', 'r', encoding='utf-8') as ef:
    env_data = json.load(ef)
conf_base = env_data.get('CONFLUENCE_BASE_URL', 'https://itpm-wiki.mos.ru/').rstrip('/')
conf_email = env_data.get('CONFLUENCE_USER_EMAIL', '')
conf_token = env_data.get('CONFLUENCE_API_TOKEN', '')

print('Confluence base:', conf_base)
print('Page ID: 738464895')

# Get page info
api = conf_base + '/rest/api'
req = urllib.request.Request(api + '/content/738464895?expand=version')
auth_str = base64.b64encode((conf_email + ':' + conf_token).encode()).decode()
req.add_header('Authorization', 'Basic ' + auth_str)
req.add_header('Accept', 'application/json')
resp = urllib.request.urlopen(req, context=ssl_ctx)
page_data = json.loads(resp.read())
print('Page title:', page_data.get('title'))

# Update page
version = page_data.get('version', {}).get('number', 1) + 1
payload = {
    'id': '738464895',
    'type': 'page',
    'title': page_data.get('title', '8170964-MosITSM. Predostavlenie dostupa k demo stenddu'),
    'space': {'key': 'DIT4ME'},
    'body': {'storage': {'value': body, 'representation': 'storage'}},
    'version': {'number': version, 'minorEdit': False}
}

req2 = urllib.request.Request(api + '/content/738464895', method='PUT')
req2.add_header('Authorization', 'Basic ' + auth_str)
req2.add_header('Content-Type', 'application/json')
req2.add_header('Accept', 'application/json')
data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
req2.data = data

try:
    resp2 = urllib.request.urlopen(req2, context=ssl_ctx)
    result = json.loads(resp2.read())
    print('Updated to v' + str(version))
    print('OK')
except Exception as e:
    print('Error: ' + str(e))
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8', errors='replace')[:500])
