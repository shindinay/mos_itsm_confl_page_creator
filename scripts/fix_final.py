#!/usr/bin/env python3
"""Исправление страницы 735538925 — точечное обновление."""
import json, re, html, urllib.request, urllib.error

ENV = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
env = json.load(open(ENV, encoding="utf-8-sig"))
base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]
PAGE_ID = "735538925"

# GET page
req = urllib.request.Request(
    base + "/rest/api/content/" + PAGE_ID + "?expand=body.storage,version",
    headers={"Authorization": "Bearer " + token}
)
resp = urllib.request.urlopen(req, timeout=15)
page_data = json.loads(resp.read().decode("utf-8"))
body = page_data["body"]["storage"]["value"]
ver = page_data["version"]["number"]
print("Current version:", ver)
print("Body length:", len(body))

# ============================================
# STEP 1: TABLE 8.1 — fill the 5 empty data rows
# ============================================
# The table has: <tr><th /></tr> + 5 rows of <tr><td></td><td></td></tr>
# We find the table and replace each <td></td> pair

table_81_rows = [
    ("Название шаблона", "mock - МосИТСМ. Предоставление/отзыв лицензии для работников"),
    ("Категория", "rfc"),
    ("Расширение UI", '2510: Предоставление прав доступа в 4me для работников (вкладка &laquo;Информация&raquo;)'),
    ("Правила автоматизации", "13 правил (см. раздел 8.1.2)"),
    ("Шаблон рабочего процесса", "16919: mock - МосИТСМ. Предоставление/отзыв лицензии для работников"),
]

# Find table after "8.1" heading
idx_81 = body.find("8.1.")
if idx_81 >= 0:
    tbl_start = body.find("<table", idx_81)
    tbl_end = body.find("</table>", tbl_start) + 8
    old_tbl = body[tbl_start:tbl_end]

    new_tbl = (
        '<table class="relative-table wrapped" style="width: 37.128%;">'
        '<colgroup><col style="width: 37.3511%;" /><col style="width: 62.5716%;" /></colgroup>'
        '<tbody><tr><th /><th /></tr>'
    )
    for label, value in table_81_rows:
        new_tbl += '<tr><td><p>' + label + '</p></td><td><p>' + value + '</p></td></tr>'
    new_tbl += '</tbody></table>'

    body = body[:tbl_start] + new_tbl + body[tbl_end:]
    print("Table 8.1 replaced")
else:
    print("Table 8.1: NOT FOUND")

# ============================================
# STEP 2: 8.1.1 — replace full MD with short description
# ============================================
# Find the full MD content inserted at 8.1.1 and truncate after "Особенности"
idx_811 = body.find("8.1.1")
if idx_811 >= 0:
    # Find where full MD ends: look for 8.1.2 marker
    idx_812 = body.find("8.1.2")
    if idx_812 >= 0:
        # Replace everything between </h3> of 8.1.1 and 8.1.2
        # Find </h3> right before "8.1.1"
        h3_end = body.rfind("</h3>", 0, idx_811)
        if h3_end >= 0:
            h3_end = h3_end + 5  # skip </h3>

            # Build short description
            short = (
                "<p>Расширение 2510 &laquo;Предоставление прав доступа в 4me для работников&raquo; — вкладка &laquo;Информация&raquo; на форме шаблона запроса.</p>"
                "<h5>Использование</h5>"
                "<p>Пользователь выбирает действие: &laquo;Предоставление прав доступа&raquo; или &laquo;Отзыв прав доступа&raquo; и заполняет пространство, статистику лицензий и список работников.</p>"
                "<h5>Особенности</h5>"
                "<p>Динамическая логика видимости полей через JavaScript. Служебные поля скрыты. Контроль количества доступных лицензий.</p>"
            )
            body = body[:h3_end] + "\n" + short + body[idx_812:]
            print("8.1.1 replaced")

# ============================================
# STEP 3: 8.1.2 — insert rules table
# ============================================
idx_812 = body.find("8.1.2")
if idx_812 >= 0:
    # Build the rules table
    ar_table = '<table><tr><th style="text-align:left;background-color:rgb(221, 221, 221)">N&#176;</th><th style="text-align:left;background-color:rgb(221, 221, 221)">ID</th><th style="text-align:left;background-color:rgb(221, 221, 221)">Название</th><th style="text-align:left;background-color:rgb(221, 221, 221)">Триггер</th><th style="text-align:left;background-color:rgb(221, 221, 221)">Суть</th><th style="text-align:left;background-color:rgb(221, 221, 221)">Карточка</th></tr>'

    rules = [
        (16207515, "Закрыть запрос при завершении РП", "on status update", "При завершении РП устанавливает статус запроса &laquo;Завершено&raquo;."),
        (16207516, "Отправка писем", "after delay", "Отправляет письмо лицам с отзываемыми ролями."),
        (16207517, "Проброс полей в задачу #4327 (откл.)", "on status update", "Передает поля в задачу #4327. Отключено."),
        (16207518, "тест подмены пространства (откл.)", "on create", "Задает пространство. Тестовое, отключено."),
        (16207519, "Закрыть запрос если переоткрыли", "on status update", "При переоткрытии восстанавливает прошлый статус."),
        (16207520, "Проброс полей в задачи", "after delay", "Копирует поля запроса в задачи РП."),
        (16207521, "Запуск проброса полей", "on create", "Запускает проброс полей через 1 секунду."),
        (16207522, "Обработка сгенерированного запроса", "on custom_fields update", "Запускает цепочку обработки после генерации."),
        (16207523, "Отмена утверждения представителей", "after delay", "Отменяет согласование, если инициатор — представитель."),
        (16207524, "Отмена пакет Внутренний", "after delay", "Отменяет задачу пакета Внутренний."),
        (16207525, "Закрытие задачи на Авто подготовку", "after delay", "Завершает задачу автоподготовки."),
        (16207526, "Завершено = Проброс коммента в задачу", "on status update", "Переносит последний комментарий в задачу РП."),
        (16207527, "Смена команды, если участник - Служебная УЗ", "on status update", "Меняет команду на jarvis, если участник — служебная УЗ."),
    ]

    for i, (rid, name, trigger, summary) in enumerate(rules, 1):
        link = "https://itsm.itsm-qa.mos.ru/automation_rules/" + str(rid)
        ar_table += '<tr><td style="text-align:left">' + str(i) + '</td>'
        ar_table += '<td style="text-align:left">' + str(rid) + '</td>'
        ar_table += '<td style="text-align:left">' + html.escape(name) + '</td>'
        ar_table += '<td style="text-align:left">' + html.escape(trigger) + '</td>'
        ar_table += '<td style="text-align:left">' + html.escape(summary) + '</td>'
        ar_table += '<td style="text-align:left"><ac:link><ri:url ri:value="' + link + '"/></ac:link></td></tr>'
    ar_table += '</table>'

    # Find the p tag right after 8.1.2 heading
    p_after_h3 = body.find("<p> /</p>", idx_812)
    if p_after_h3 >= 0:
        # Replace the first empty <p> after 8.1.2 with the table
        insert_text = '<p>13 правил автоматизации на шаблоне запроса:</p>' + ar_table
        body = body[:p_after_h3] + insert_text + body[p_after_h3 + len("<p> /</p>"):]
        print("8.1.2 inserted")
    else:
        print("8.1.2: p tag NOT FOUND")

# ============================================
# STEP 4: 8.2.1 and 8.2.2 — insert "Отсутствует"/"Отсутствуют"
# ============================================
# Find 8.2.1 and 8.2.2 and replace their <p> /</p>
for section, text in [("8.2.1", "<p>Отсутствует (у РП 16919 нет своего UI-расширения)</p>"),
                      ("8.2.2", "<p>Отсутствуют (у РП 16919 нет правил автоматизации)</p>")]:
    idx = body.find(section)
    if idx >= 0:
        p_after = body.find("<p> /</p>", idx)
        if p_after >= 0:
            body = body[:p_after] + text + body[p_after + len("<p> /</p>"):]
            print(section + " replaced")
        else:
            print(section + ": p tag NOT FOUND")
    else:
        print(section + ": section NOT FOUND")

# ============================================
# STEP 5: 8.3 — verify task_template_name is filled
# ============================================
if "3698: Согласование" in body:
    print("8.3 task_template_name OK")
else:
    # Replace placeholder span
    idx_tm = body.find("task_template_name")
    if idx_tm >= 0:
        body = body[:idx_tm] + "3698: Согласование с владельцем/представителем пространства. Предоставление/отзыв лицензии для работников; 7337: Авто подготовка РП; 29151: Авто подготовка РП. Предоставление/отзыв лицензии" + body[idx_tm + len("task_template_name"):]
        print("8.3 task_template_name replaced")

# ============================================
# STEP 6: Fix unescaped &
# ============================================
def fix_amp(match):
    tag_type = match.group(1)
    content = match.group(2)
    content = re.sub(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', r'&amp;', content)
    return '<' + tag_type + '>' + content + '</' + tag_type + '>'

body = re.sub(r'<(p|td|th)([^>]*)>(.*?)</\1>', fix_amp, body, flags=re.DOTALL)

amp_count = len(re.findall(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', body))
print("Unescaped & count:", amp_count)

# ============================================
# Verify
# ============================================
print("\n=== VERIFICATION ===")

# Table 8.1
for t in ["rfc", "2510:", "13 правил", "16919:"]:
    if t in body:
        print("Table 8.1 OK: " + t)
    else:
        print("Table 8.1 MISSING: " + t)

# 8.1.1
if "8.1.1" in body:
    idx = body.find("8.1.1")
    after = body[idx:idx+300]
    if "2510" in after and "Предоставление прав доступа в 4me для работников" in after and len(after) < 500:
        print("8.1.1 OK: short description")
    else:
        print("8.1.1 CHECK: " + repr(after[:200]))

# 8.1.2
if "8.1.2" in body:
    idx = body.find("8.1.2")
    after = body[idx:idx+500]
    if "16207515" in after:
        print("8.1.2 OK")
    else:
        print("8.1.2 CHECK: " + repr(after[:200]))

# 8.2.1
if "8.2.1" in body:
    idx = body.find("8.2.1")
    after = body[idx:idx+200]
    if "Отсутствует" in after:
        print("8.2.1 OK")
    else:
        print("8.2.1 CHECK: " + repr(after[:100]))

# 8.2.2
if "8.2.2" in body:
    idx = body.find("8.2.2")
    after = body[idx:idx+200]
    if "Отсутствуют" in after:
        print("8.2.2 OK")
    else:
        print("8.2.2 CHECK: " + repr(after[:100]))

# Layout balance
ac_open = body.count("<ac:layout-cell>")
ac_close = body.count("</ac:layout-cell>")
print("ac:layout-cell: " + str(ac_open) + " / " + str(ac_close) + (" OK" if ac_open == ac_close else " UNBALANCED!"))

print("Body length:", len(body))

# ============================================
# PUT
# ============================================
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
    print("\nPUT SUCCESS! Version:", result["version"]["number"])
    print("URL:", result["_links"]["base"] + result["_links"]["webui"])
except urllib.error.HTTPError as e:
    print("\nPUT ERROR:", e.code)
    err = e.read().decode("utf-8")
    print(err[:2000])
except Exception as e:
    print("\nPUT ERROR:", e)
