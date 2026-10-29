#!/usr/bin/env python3
"""Исправление страницы 735538925 — финальная точечная версия."""
import json, re, html, urllib.request, urllib.error

ENV = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
env = json.load(open(ENV, encoding="utf-8-sig"))
base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]
PAGE_ID = "735538925"

# GET page (version 8)
req = urllib.request.Request(
    base + "/rest/api/content/" + PAGE_ID + "?expand=body.storage,version",
    headers={"Authorization": "Bearer " + token}
)
resp = urllib.request.urlopen(req, timeout=15)
page_data = json.loads(resp.read().decode("utf-8"))
body = page_data["body"]["storage"]["value"]
ver = page_data["version"]["number"]
print("Current version:", ver)

# ========================================
# STEP 1: Table 8.1 — replace empty cells
# ========================================
# Pattern: <tr><td></td><td></td></tr> in the table near 8.1
# We replace row-by-row using index-based replacement

# The table has rows for: Название шаблона, Категория, Расширение UI, Правила автоматизации, Шаблон рабочего процесса

# Replace first data row (Название шаблона)
old_r1 = '<tr><td></td><td></td></tr>'
new_r1 = '<tr><td><p>Название шаблона</p></td><td><p>mock - МосИТСМ. Предоставление/отзыв лицензии для работников</p></td></tr>'
body = body.replace(old_r1, new_r1, 1)
print("Row 1 (Название шаблона) replaced")

# Replace second data row (Категория)
body = body.replace(old_r1, '<tr><td><p>Категория</p></td><td><p>rfc</p></td></tr>', 1)
print("Row 2 (Категория) replaced")

# Replace third data row (Расширение UI)
body = body.replace(old_r1, '<tr><td><p>Расширение UI</p></td><td><p>2510: Предоставление прав доступа в 4me для работников (вкладка &laquo;Информация&raquo;)</p></td></tr>', 1)
print("Row 3 (Расширение UI) replaced")

# Replace fourth data row (Правила автоматизации)
body = body.replace(old_r1, '<tr><td><p>Правила автоматизации</p></td><td><p>13 правил (см. раздел 8.1.2)</p></td></tr>', 1)
print("Row 4 (Правила автоматизации) replaced")

# Replace fifth data row (Шаблон рабочего процесса)
body = body.replace(old_r1, '<tr><td><p>Шаблон рабочего процесса</p></td><td><p>16919: mock - МосИТСМ. Предоставление/отзыв лицензии для работников</p></td></tr>', 1)
print("Row 5 (Шаблон рабочего процесса) replaced")

# Verify table 8.1
for t in ["rfc", "2510:", "13 правил", "16919:"]:
    if t in body:
        print("  Table OK: " + t)
    else:
        print("  Table FAIL: " + t)

# ========================================
# STEP 2: 8.1.1 — replace full MD with short description
# ========================================
# Find: "8.1.1." heading and replace everything until "8.1.2"
idx_811 = body.find("8.1.1")
idx_812 = body.find("8.1.2")

if idx_811 >= 0 and idx_812 >= 0:
    # Find the </h3> of 8.1.1 heading
    h3_start = body.rfind("</h3>", 0, idx_811)
    if h3_start >= 0:
        h3_end = h3_start + 5  # </h3> length

        # Build short description
        short_811 = (
            "<p>Расширение 2510 &laquo;Предоставление прав доступа в 4me для работников&raquo; — вкладка &laquo;Информация&raquo; на форме шаблона запроса.</p>"
            "<h5>Использование</h5>"
            "<p>Пользователь открывает форму и выбирает действие: &laquo;Предоставление прав доступа&raquo; или &laquo;Отзыв прав доступа&raquo;. После выбора отображаются соответствующие блоки: пространство (из представленных, где пользователь &mdash; владелец), статистика лицензий и список работников (для предоставления) или лицензий на отзыв (для отзыва).</p>"
            "<h5>Особенности</h5>"
            "<p>Динамическая логика видимости полей через JavaScript. Служебные поля (инициатор, лица для отзыва, авто-отзыв) скрыты и используются внутренними правилами. Контроль количества доступных лицензий с выводом предупреждения при недостатке.</p>"
        )

        # Remove everything between </h3> of 8.1.1 and the start of 8.1.2, insert short content
        body = body[:h3_end] + "\n" + short_811 + "\n" + body[idx_812:]
        print("8.1.1 replaced with short description")
    else:
        print("8.1.1: </h3> NOT FOUND")
else:
    print("8.1.1/8.1.2 NOT FOUND")

# ========================================
# STEP 3: 8.1.2 — insert rules table
# ========================================
idx_812_h3 = body.find("8.1.2")
if idx_812_h3 >= 0:
    # Find the </h3> of 8.1.2 heading
    h3_end_812 = body.find("</h3>", idx_812_h3)
    if h3_end_812 >= 0:
        # Build the rules table
        ar_table = '<table><tr>'
        ar_table += '<th style="text-align:left;background-color:rgb(221, 221, 221)">N&#176;</th>'
        ar_table += '<th style="text-align:left;background-color:rgb(221, 221, 221)">ID</th>'
        ar_table += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Название</th>'
        ar_table += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Триггер</th>'
        ar_table += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Суть</th>'
        ar_table += '<th style="text-align:left;background-color:rgb(221, 221, 221)">Карточка</th></tr>'

        rule_data = [
            (16207515, "Закрыть запрос при завершении РП", "on status update", "При изменении статуса проверяет завершение РП, устанавливает статус запроса &laquo;Завершено&raquo;."),
            (16207516, "Отправка писем", "after delay", "Отправляет письмо лицам с отзываемыми ролями, если есть хотя бы одна активная учетная запись."),
            (16207517, "Проброс полей в задачу #4327 (отключено)", "on status update", "Передает поля account и people_for_revoke в задачу #4327 при статусе assigned. Отключено."),
            (16207518, "тест подмены пространства (отключено)", "on create", "Задает пространство new_account. Тестовое, отключено."),
            (16207519, "Закрыть запрос если переоткрыли", "on status update", "При переоткрытии ранее завершенного запроса восстанавливает прошлый статус и добавляет предупреждение."),
            (16207520, "Проброс полей в задачи", "after delay", "Копирует поля запроса в задачи РП, формирует список лиц и ссылку на справочник."),
            (16207521, "Запуск проброса полей", "on create", "Если задача не сгенерирована, запускает правило проброса полей."),
            (16207522, "Обработка сгенерированного запроса", "on custom_fields update", "Запускает цепочку правил обработки после генерации запроса."),
            (16207523, "Отмена утверждения представителей", "after delay", "Если инициатор — представитель пространства, отменяет задачу согласования."),
            (16207524, "Отмена пакет Внутренний", "after delay", "Отменяет задачу пакета Внутренний, если пространство не ism."),
            (16207525, "Закрытие задачи на Авто подготовку", "after delay", "Завершает задачу автоподготовки, если она еще не завершена."),
            (16207526, "Завершено = Проброс коммента в задачу", "on status update", "При завершении запроса переносит последний комментарий в задачу РП."),
            (16207527, "Смена команды, если участник - Служебная УЗ", "on status update", "При завершении: если участник — служебная УЗ, меняет команду на jarvis."),
        ]

        for i, (rid, name, trigger, summary) in enumerate(rule_data, 1):
            link = "https://itsm.itsm-qa.mos.ru/automation_rules/" + str(rid)
            ar_table += "<tr>"
            ar_table += '<td style="text-align:left">' + str(i) + "</td>"
            ar_table += '<td style="text-align:left">' + str(rid) + "</td>"
            ar_table += '<td style="text-align:left">' + html.escape(name) + "</td>"
            ar_table += '<td style="text-align:left">' + html.escape(trigger) + "</td>"
            ar_table += '<td style="text-align:left">' + html.escape(summary) + "</td>"
            ar_table += '<td style="text-align:left"><ac:link><ri:url ri:value="' + link + '"/></ac:link></td>'
            ar_table += "</tr>"
        ar_table += "</table>"

        insert_text = "<p>13 правил автоматизации на шаблоне запроса:</p>" + ar_table

        # Find what comes after </h3> of 8.1.2 — likely a <p> with placeholder span
        after_h3 = body[h3_end_812:]
        # Find the next h2 or h3 to insert before
        next_h2 = re.search(r"</h3>\s*(<h2)", after_h3)
        if next_h2:
            insert_at = h3_end_812 + next_h2.start()
            body = body[:insert_at] + insert_text + body[insert_at:]
            print("8.1.2 rules table inserted")
        else:
            print("8.1.2: no next section heading found")

# ========================================
# STEP 4: 8.2.1 — insert "Отсутствует"
# ========================================
idx_821 = body.find("8.2.1")
if idx_821 >= 0:
    h3_end = body.find("</h3>", idx_821)
    if h3_end >= 0:
        after = body[h3_end:]
        next_h = re.search(r"</h3>\s*(<h2)", after)
        if next_h:
            insert_at = h3_end + next_h.start()
            body = body[:insert_at] + '<p>Отсутствует (у РП 16919 нет своего UI-расширения)</p>' + body[insert_at:]
            print("8.2.1 replaced")
        else:
            print("8.2.1: no next h2 found")
    else:
        print("8.2.1: </h3> not found")
else:
    print("8.2.1: NOT FOUND")

# ========================================
# STEP 5: 8.2.2 — insert "Отсутствуют"
# ========================================
idx_822 = body.find("8.2.2")
if idx_822 >= 0:
    h3_end = body.find("</h3>", idx_822)
    if h3_end >= 0:
        after = body[h3_end:]
        next_h = re.search(r"</h3>\s*(<h2)", after)
        if next_h:
            insert_at = h3_end + next_h.start()
            body = body[:insert_at] + '<p>Отсутствуют (у РП 16919 нет правил автоматизации)</p>' + body[insert_at:]
            print("8.2.2 replaced")
        else:
            print("8.2.2: no next h2 found")
    else:
        print("8.2.2: </h3> not found")
else:
    print("8.2.2: NOT FOUND")

# ========================================
# STEP 6: 8.3 — replace task_template_name
# ========================================
idx_tm = body.find("task_template_name")
if idx_tm >= 0:
    body = body[:idx_tm] + "3698: Согласование с владельцем/представителем пространства. Предоставление/отзыв лицензии для работников; 7337: Авто подготовка РП; 29151: Авто подготовка РП. Предоставление/отзыв лицензии" + body[idx_tm + len("task_template_name"):]
    print("8.3 task_template_name replaced")
else:
    print("8.3 task_template_name NOT FOUND")

# ========================================
# STEP 7: Fix unescaped &
# ========================================
def fix_amp(match):
    tag_type = match.group(1)
    content = match.group(2)
    content = re.sub(r"&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)", r"&amp;", content)
    return "<" + tag_type + ">" + content + "</" + tag_type + ">"

body = re.sub(r"<(p|td|th)([^>]*)>(.*?)</\1>", fix_amp, body, flags=re.DOTALL)

amp_count = len(re.findall(r"&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)", body))
print("Unescaped & count:", amp_count)

# ========================================
# Verify
# ========================================
print()
print("=== VERIFICATION ===")

# Check table 8.1
for t in ["rfc", "2510:", "13 правил", "16919:"]:
    if t in body:
        print("Table 8.1 OK: " + t)
    else:
        print("Table 8.1 MISSING: " + t)

# Check 8.1.1
if "8.1.1" in body:
    idx = body.find("8.1.1")
    after = body[idx:idx+300]
    if "2510" in after and "Использование" in after:
        print("8.1.1 OK")
    else:
        print("8.1.1 CHECK: " + repr(after[:150]))

# Check 8.1.2
if "8.1.2" in body:
    idx = body.find("8.1.2")
    after = body[idx:idx+300]
    if "16207515" in after:
        print("8.1.2 OK")
    else:
        print("8.1.2 CHECK: " + repr(after[:150]))

# Check 8.2.1
if "8.2.1" in body:
    idx = body.find("8.2.1")
    after = body[idx:idx+200]
    if "Отсутствует" in after:
        print("8.2.1 OK")
    else:
        print("8.2.1 CHECK: " + repr(after[:100]))

# Check 8.2.2
if "8.2.2" in body:
    idx = body.find("8.2.2")
    after = body[idx:idx+200]
    if "Отсутствуют" in after:
        print("8.2.2 OK")
    else:
        print("8.2.2 CHECK: " + repr(after[:100]))

# Check 8.3
if "3698: Согласование" in body:
    print("8.3 task_template_name OK")
else:
    print("8.3 task_template_name MISSING")

# Check no remaining placeholders
for var in ["req_ui_ext_ai_desc", "req_template_automation_rule_ai_description", "wf_ui_ext_desc", "wf_ar_desc", "task_template_name", "req_template_subj"]:
    if '<span class="templateparameter">(' + var + ')</span>' in body:
        print("PLACEHOLDER STILL: " + var)
    else:
        print("Placeholder OK: " + var)

print()
print("Body length:", len(body))

# Check layout balance
ac_open = body.count("<ac:layout-cell>")
ac_close = body.count("</ac:layout-cell>")
print("ac:layout-cell balanced:", ac_open, "==", ac_close)

# ========================================
# PUT
# ========================================
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
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    method="PUT"
)

try:
    resp_put = urllib.request.urlopen(req_put, timeout=30)
    result = json.loads(resp_put.read().decode("utf-8"))
    print()
    print("PUT SUCCESS! Version:", result["version"]["number"])
    print("URL:", result["_links"]["base"] + result["_links"]["webui"])
except urllib.error.HTTPError as e:
    print("PUT ERROR:", e.code)
    err = e.read().decode("utf-8")
    print(err[:2000])
except Exception as e:
    print("PUT ERROR:", e)
