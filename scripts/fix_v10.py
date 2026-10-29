#!/usr/bin/env python3
"""Исправление страницы 735538925: читаем v8_body, применяем замены, PUT в Confluence."""
import json, re, html, urllib.request, urllib.error

# ---- LOAD ENV ----
ENV_FILE = r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\.env"
with open(ENV_FILE, encoding="utf-8-sig") as f:
    env = json.load(f)
base = env["CONFLUENCE_BASE_URL"].rstrip("/")
token = env["CONFLUENCE_API_TOKEN"]
PAGE_ID = "735538925"

# ---- READ ORIGINAL V8 BODY ----
with open(r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\temp\v8_body.html", encoding="utf-8") as f:
    body = f.read()

print("Original length:", len(body))

# ---- STEP 1: TABLE 8.1 ----
# The table is between "<h2>8.1. Шаблон запроса mock..." and "<h3>8.1.1"
# Find it by looking for the table after "8.1." heading
idx_start = body.find("<h2><span class=\"numhead-number\">8.1. </span>")
if idx_start < 0:
    idx_start = body.find("8.1. </span>")
# Find the table after that heading
tbl_start = body.find("<table", idx_start)
# Find the table end just before the <h3>8.1.1</h3>
idx_h3_811 = body.find("<h3><span class=\"numhead-number\">8.1.1. </span>")
tbl_end = body.find("</table>", tbl_start)
# Verify it's before 8.1.1
if tbl_end > idx_h3_811:
    print("WARNING: Table end is after 8.1.1 heading, something is wrong")
else:
    print("Found table 8.1: start=%d, end=%d" % (tbl_start, tbl_end))

    new_tbl = (
        '<table class="relative-table wrapped" style="width: 37.128%;">'
        '<colgroup><col style="width: 37.3511%;" /><col style="width: 62.5716%;" /></colgroup>'
        '<tbody><tr><th /><th /></tr>'
    )
    rows = [
        ("Название шаблона", "mock - МосИТСМ. Предоставление/отзыв лицензии для работников"),
        ("Категория", "rfc"),
        ("Расширение UI", "2510: Предоставление прав доступа в 4me для работников (вкладка &laquo;Информация&raquo;)"),
        ("Правила автоматизации", "13 правил (см. раздел 8.1.2)"),
        ("Шаблон рабочего процесса", "16919: mock - МосИТСМ. Предоставление/отзыв лицензии для работников"),
    ]
    for label, value in rows:
        new_tbl += '<tr><td><p>' + label + '</p></td><td><p>' + value + '</p></td></tr>'
    new_tbl += '</tbody></table>'

    body = body[:tbl_start] + new_tbl + body[tbl_end:]
    print("Table 8.1 replaced")

# ---- STEP 2: 8.1.1 + 8.1.2 + 8.2.1 + 8.2.2 ----
# Find the start of 8.1.1 content and end before 8.3.2
idx_h3_811 = body.find("<h3><span class=\"numhead-number\">8.1.1. </span>")
idx_h3_832 = body.find("<h3><span class=\"numhead-number\">8.3.2. </span>")
print("8.1.1 heading at: %d" % idx_h3_811)
print("8.3.2 heading at: %d" % idx_h3_832)

if idx_h3_811 >= 0 and idx_h3_832 >= 0:
    # 8.1.1 heading ends with </h3>
    h3_end_811 = body.find("</h3>", idx_h3_811)
    if h3_end_811 >= 0:
        # Content of 8.1.1 starts after </h3>
        # We replace from after </h3> to before <h3>8.3.2</h3>
        content_start = h3_end_811 + 5
        # Find the </h3> of 8.3.2 to know where the heading ends
        content_end = idx_h3_832

        # Build replacement content
        # 8.1.1 short description
        part_811 = (
            "<p>Расширение 2510 &laquo;Предоставление прав доступа в 4me для работников&raquo; — вкладка &laquo;Информация&raquo; на форме шаблона запроса.</p>"
            "<p>Пользователь выбирает действие: &laquo;Предоставление прав доступа&raquo; или &laquo;Отзыв прав доступа&raquo; и заполняет пространство, статистику лицензий и список работников.</p>"
            "<p>Динамическая логика видимости полей через JavaScript. Служебные поля скрыты. Контроль количества доступных лицензий.</p>"
        )

        # 8.1.2 rules table
        rules_table = '<table class="relative-table wrapped" style="width: 85%;">'
        rules_table += '<colgroup><col style="width: 4%;" /><col style="width: 10%;" /><col style="width: 20%;" /><col style="width: 15%;" /><col style="width: 35%;" /><col style="width: 16%;" /></colgroup>'
        rules_table += '<tbody><tr><th><p>N&#176;</p></th><th><p>ID</p></th><th><p>Название</p></th><th><p>Триггер</p></th><th><p>Суть</p></th><th><p>Карточка</p></th></tr>'

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
            rules_table += '<tr><td><p>' + str(i) + '</p></td>'
            rules_table += '<td><p>' + str(rid) + '</p></td>'
            rules_table += '<td><p>' + html.escape(name) + '</p></td>'
            rules_table += '<td><p>' + html.escape(trigger) + '</p></td>'
            rules_table += '<td><p>' + html.escape(summary) + '</p></td>'
            rules_table += '<td><p><ac:link><ri:url ri:value="' + link + '"/></ac:link></p></td></tr>'
        rules_table += '</tbody></table>'

        part_812 = (
            '<h3><span class="numhead-number">8.1.2. </span>Требования к правилам автоматизации</h3>'
            '<p>13 правил автоматизации на шаблоне запроса:</p>'
        ) + rules_table

        # 8.2.1
        part_821 = (
            '<h3><span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3>'
            '<p>Отсутствует (у РП 16919 нет своего UI-расширения).</p>'
        )

        # 8.2.2
        part_822 = (
            '<h3><span class="numhead-number">8.2.2. </span>Требования к правилам автоматизации</h3>'
            '<p>Отсутствуют (у РП 16919 нет правил автоматизации).</p>'
        )

        replacement = part_811 + "\n" + part_812 + "\n" + part_821 + "\n" + part_822

        body = body[:content_start] + replacement + body[content_end:]
        print("Replaced content between 8.1.1 and 8.3.2")

# ---- STEP 3: FIX AMPERSANDS ----
def fix_ampersands_in_tags(text):
    """Replace bare & with &amp; inside HTML tags."""
    def replace_in_tag(match):
        tag_type = match.group(1)
        content = match.group(2)
        # Replace bare & that aren't already entities
        fixed = re.sub(r'&(?!#|lt;|gt;|amp;|quot;|nbsp;|[a-z]+;)', r'&amp;', content)
        return '<' + tag_type + '>' + fixed + '</' + tag_type + '>'
    text = re.sub(r'<(p|td|th|span|li|tr|div|table|tbody|colgroup)[^>]*>(.*?)</\1>', replace_in_tag, text, flags=re.DOTALL)
    return text

body = fix_ampersands_in_tags(body)

# ---- VERIFICATION ----
print("\n=== VERIFICATION ===")

# Check layout balance
ac_open = body.count("<ac:layout-cell>")
ac_close = body.count("</ac:layout-cell>")
print("ac:layout-cell: %d / %d %s" % (ac_open, ac_close, "OK" if ac_open == ac_close else "UNBALANCED!"))

# Check h3 balance
h3_open = len(re.findall(r'<h3[^>]*>', body))
h3_close = body.count("</h3>")
print("h3: %d / %d %s" % (h3_open, h3_close, "OK" if h3_open == h3_close else "UNBALANCED!"))

# Check table balance
tbl_open = body.count("<table")
tbl_close = body.count("</table>")
print("table: %d / %d %s" % (tbl_open, tbl_close, "OK" if tbl_open == tbl_close else "UNBALANCED!"))

# Check key content
checks = [
    ("Table 8.1: rfc", "rfc" in body),
    ("Table 8.1: 2510:", "2510:" in body),
    ("Table 8.1: 13 правил", "13 правил" in body),
    ("Table 8.1: 16919:", "16919:" in body),
    ("8.1.1: short desc", "Предоставление прав доступа в 4me" in body),
    ("8.1.2: rules table", "16207515" in body),
    ("8.2.1: отсутствует", "8.2.1." in body and "Отсутствует" in body),
    ("8.2.2: отсутствуют", "8.2.2." in body and "Отсутствуют" in body),
]

for label, result in checks:
    print("%s: %s" % (label, "OK" if result else "MISSING"))

print("Final body length:", len(body))

# ---- PUT TO CONFLUENCE ----
# First get current version
req_get = urllib.request.Request(
    base + "/rest/api/content/" + PAGE_ID + "?expand=version",
    headers={"Authorization": "Bearer " + token}
)
resp_get = urllib.request.urlopen(req_get, timeout=15)
page_data = json.loads(resp_get.read().decode("utf-8"))
new_ver = page_data["version"]["number"] + 1

put_data = {
    "id": PAGE_ID,
    "type": "page",
    "title": page_data["title"],
    "version": {"number": new_ver, "minorEdit": False},
    "body": {"storage": {"value": body, "representation": "storage"}},
}

print("\nPUT to Confluence, version %d" % new_ver)
req_put = urllib.request.Request(
    base + "/rest/api/content/" + PAGE_ID,
    data=json.dumps(put_data).encode("utf-8"),
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    method="PUT"
)

try:
    resp_put = urllib.request.urlopen(req_put, timeout=30)
    result = json.loads(resp_put.read().decode("utf-8"))
    print("SUCCESS! New version:", result["version"]["number"])
    print("URL:", result["_links"]["base"] + result["_links"]["webui"])
except urllib.error.HTTPError as e:
    print("ERROR: HTTP %d" % e.code)
    err = e.read().decode("utf-8")
    print(err[:2000])
except Exception as e:
    print("ERROR: %s" % str(e))
