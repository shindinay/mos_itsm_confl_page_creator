#!/usr/bin/env python3
"""Сохраняет промежуточный результат body для анализа."""
import json, re, html

# ---- READ ORIGINAL V8 BODY ----
with open(r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\temp\v8_body.html", encoding="utf-8") as f:
    body = f.read()

print("Original length:", len(body))

# ---- STEP 1: TABLE 8.1 ----
idx_start = body.find("8.1. </span>")
tbl_start = body.find("<table", idx_start)
idx_h3_811 = body.find("<h3><span class=\"numhead-number\">8.1.1. </span>")
tbl_end = body.find("</table>", tbl_start)

if tbl_end > idx_h3_811:
    print("WARNING: Table end is after 8.1.1 heading")
else:
    print("Found table 8.1: start=%d, end=%d" % (tbl_start, tbl_end))
    print("Table content preview (0:100): " + body[tbl_start:tbl_start+100])
    print("After table (end:end+50): " + body[tbl_end:tbl_end+50])

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
    print("Table 8.1 replaced. New length:", len(body))

# ---- STEP 2: Find boundaries ----
idx_h3_811 = body.find("<h3><span class=\"numhead-number\">8.1.1. </span>")
idx_h3_832 = body.find("<h3><span class=\"numhead-number\">8.3.2. </span>")
print("8.1.1 heading at: %d" % idx_h3_811)
print("8.3.2 heading at: %d" % idx_h3_832)

if idx_h3_811 >= 0 and idx_h3_832 >= 0:
    h3_end_811 = body.find("</h3>", idx_h3_811)
    print("8.1.1 </h3> at: %d" % h3_end_811)
    print("Content before replacement (h3_end_811:end of 8.3.2):")
    preview = body[h3_end_811:h3_end_811+100]
    print("After 8.1.1 </h3>: " + repr(preview))
    print("Before 8.3.2:")
    preview2 = body[idx_h3_832-50:idx_h3_832]
    print(repr(preview2))

    # Check what tags are around 8.3.2
    # Look for <p> tags before 8.3.2
    p_before = body.rfind("<p>", 0, idx_h3_832)
    print("Last <p> before 8.3.2 at: %d" % p_before)
    if p_before >= 0:
        print("After last <p>: " + repr(body[p_before:p_before+20]))

# Check table counts
print("\n=== TABLE COUNTS ===")
print("<table count:", body.count("<table"))
print("</table> count:", body.count("</table>"))

# Find all <table positions
import re
for m in re.finditer(r'<table', body):
    pos = m.start()
    preview = body[pos:pos+80]
    print("  <table at %d: %s..." % (pos, preview[:60]))

# ---- Save body to file for analysis ----
with open(r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_confl_page_creator\temp\body_step1.html", encoding="utf-8") as f:
    f.write(body)
print("\nBody saved to body_step1.html")
