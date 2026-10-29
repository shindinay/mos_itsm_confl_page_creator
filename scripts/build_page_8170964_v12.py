# -*- coding: utf-8 -*-
"""Сборка тела страницы Confluence по правилам v1.2 (28.10.2026) для RFC 8170964.

Источники:
- template_body.html (свежая редакция корпоративного шаблона, 13 плейсхолдеров)
- artifact request_vars_8170964_20261028_134841.json (данные запроса)
- structure_56363_20261028_134057.json (структура шаблона 56363)
- desc_14567.md (UI-расширение) — переиспользуется конвертация из прошлого
  прогона (page_body_8170964.html, опубликована без ошибок) с контрольными фразами

Результат: temp/page_body_8170964_v12.html + temp/payload_8170964_v12.json
"""
import io, json, re, os, sys
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(SKILL)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---------------------------------------------------------------- данные
req = json.load(open(r"C:\Alex\_PRJ\2_MosITSM Automation Prj\mos_itsm_get_obj_structure\artifact\request_vars_8170964_20261028_134841.json", encoding="utf-8-sig"))["request_variables"]
RV = {
    "id": str(req["request.id"]),
    "uri": req["request.uri"],
    "subject": req["request.subject"],
    "requested_for": req["request.requested_for"],
    "created_at": req["request.created_at"],
    "first_comment": req["request.notes[first]"],
}
assert RV["id"] == "8170964", RV["id"]
assert RV["uri"] == "https://itsm.itsm-qa.mos.ru/requests/8170964"

TPL_SUBJ = "МосИТСМ. Предоставление доступа к демо стенду"
TPL_ACCOUNT = "Каталог услуг Правительства Москвы (itsm)"
CATEGORY = "rfc"
WF_ID, WF_NAME = "15785", TPL_SUBJ
UIEXT_ID, UIEXT_NAME = "14567", "Предоставление демо стенда"
PROFILE = ('<ac:structured-macro ac:name="profile">'
           '<ac:parameter ac:name="user">'
           '<ri:user ri:userkey="2c98d8026e1c34cb016e45ea6c064b40" />'
           '</ac:parameter></ac:structured-macro>')
REQ_LINK = '<a href="%s">RFC %s</a>' % (RV["uri"], RV["id"])  # v1.2 правило 7

body = open("template_body.html", encoding="utf-8").read()

def replace_input(name, value):
    """Заменить <input ... variableValues.NAME .../> + <span class=templateparameter>(NAME)</span>."""
    global body
    pat = re.compile(r'<input type="text" name="variableValues\.%s" size="12" class="page-template-field" disabled=""/> <span class="templateparameter">\(%s\)</span>' % (name, name))
    n = len(pat.findall(body))
    assert n == 1, "placeholder %s: %d matches" % (name, n)
    body = pat.sub(lambda m: value, body, count=1)

def replace_img(name, value):
    """Заменить <span class="confluence-embedded-file-wrapper"><img ... template-variable?name=NAME ...></span>."""
    global body
    pat = re.compile(r'<span class="confluence-embedded-file-wrapper"><img [^>]*template-variable\?name=%s[^>]*/?>\s*</span>' % name)
    n = len(pat.findall(body))
    assert n == 1, "img placeholder %s: %d matches" % (name, n)
    body = pat.sub(lambda m: value, body, count=1)

# ---------------------------------------------------------------- раздел 1: История изменений
replace_input("rfc_id", esc(RV["id"]))
replace_input("req_created_at", esc(RV["created_at"]))
replace_input("req_requested_for", esc(RV["requested_for"]))
# Автор требования (последняя ячейка строки истории, за ней закрывается tbody)
AUTH_CELL = '<td class="confluenceTd"><div class="content-wrapper"><p><br/></p></div></td></tr></tbody>'
NEW_AUTH_CELL = ('<td class="confluenceTd"><div class="content-wrapper"><p>%s</p></div></td></tr></tbody>' % PROFILE)
assert body.count(AUTH_CELL) == 1, "author cell not unique"
body = body.replace(AUTH_CELL, NEW_AUTH_CELL, 1)

# ---------------------------------------------------------------- раздел 3: Общие сведения
replace_input("req_subject", esc(RV["subject"]))
replace_input("req_uri", REQ_LINK)              # v1.2: видимая гиперссылка RFC N
replace_input("req_id", esc(RV["id"]))
replace_img("req_template_account", esc(TPL_ACCOUNT))
replace_img("confluence_token_owner", PROFILE)  # автор — макрос профиля (userkey ShindinAY)

# ---------------------------------------------------------------- раздел 6.1: Изначальная постановка
replace_input("req_first_comment", esc(RV["first_comment"]))

# ---------------------------------------------------------------- раздел 8.1: Шаблон запроса
OLD_H2_81 = ('<h2 id="DIT4ME-Шаблонзапроса(req_template_subj)"><span class="numhead-number">8.1. </span>'
             'Шаблон запроса <input type="text" name="variableValues.req_template_subj" size="12" class="page-template-field" disabled=""/> '
             '<span class="templateparameter">(req_template_subj)</span></h2>')
NEW_H2_81 = ('<h2 id="DIT4ME-Шаблонзапроса"><span class="numhead-number">8.1. </span>'
             'Шаблон запроса %s</h2>' % esc(TPL_SUBJ))
assert body.count(OLD_H2_81) == 1, "h2 8.1 not found"
body = body.replace(OLD_H2_81, NEW_H2_81, 1)

def fill_param_row(label, value_html, wrapper):
    """Заполнить пустую ячейку в таблице параметров 8.1. wrapper: 'p' | 'br'."""
    global body
    if wrapper == "p":
        old = ('<tr><td class="confluenceTd"><p>%s</p></td>'
               '<td class="confluenceTd"><div class="content-wrapper"><p><br/></p></div></td></tr>' % label)
        new = ('<tr><td class="confluenceTd"><p>%s</p></td>'
               '<td class="confluenceTd"><div class="content-wrapper"><p>%s</p></div></td></tr>' % (label, value_html))
    else:
        old = ('<tr><td class="confluenceTd"><p>%s</p></td>'
               '<td class="confluenceTd"><br/></td></tr>' % label)
        new = ('<tr><td class="confluenceTd"><p>%s</p></td>'
               '<td class="confluenceTd">%s</td></tr>' % (label, value_html))
    assert body.count(old) == 1, "param row not unique: %s" % label
    body = body.replace(old, new, 1)

fill_param_row("Название шаблона", esc(TPL_SUBJ), "p")
fill_param_row("Категория", esc(CATEGORY), "br")
fill_param_row("Расширение UI",
    '%s: %s (вкладка «Информация», <ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/ui_extensions/%s" /></ac:link>)'
    % (UIEXT_ID, esc(UIEXT_NAME), UIEXT_ID), "br")
fill_param_row("Правила автоматизации",
    "10 правил: 3 на шаблоне запроса (раздел 8.1.2), 7 на задачах рабочего процесса %s (раздел 8.3)"
    % esc(WF_ID), "br")
fill_param_row("Шаблон рабочего процесса",
    '%s: %s (<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/workflow_templates/%s" /></ac:link>)'
    % (WF_ID, esc(WF_NAME), WF_ID), "br")

# ---------------------------------------------------------------- 8.1.1: полное описание расширения 14567
# Переиспользуем конвертацию desc_14567.md из прошлого прогона (страница опубликована без ошибок)
old = open("page_body_8170964.html", encoding="utf-8").read()
m1 = old.find('<h3 id="DIT4ME-ТребованиякРасширениюUI">')
m2 = old.find('<h3 id="DIT4ME-Требованиякправиламавтоматизации">')
assert m1 != -1 and m2 != -1 and m1 < m2
h3_end = old.find('</h3>', m1) + len('</h3>')
chunk = old[h3_end:m2]
assert chunk.startswith('<p>'), chunk[:50]
chunk = chunk[len('<p>'):]
assert chunk.rstrip().endswith('</p>'), chunk[-80:]
chunk = chunk.rstrip()[: -len('</p>')]
# контрольные фразы из desc_14567.md — сверка с исходником описания
for phrase in ["Первичное создание описания расширения (расширение 14567)",
               "лица_без_локальных",
               "Активная версия 8 (id 174007); подготовлена версия 9 (id 210117), не активирована",
               "Атрибут data-internal скрывает секцию «Запрос в р-сервис» от обычных пользователей"]:
    assert phrase in chunk, "phrase missing in desc chunk: %s" % phrase
assert "<c " not in chunk and "**" not in chunk
# вставляем вместо плейсхолдера req_ui_ext_ai_desc
OLD_811 = ('<h3 id="DIT4ME-ТребованиякРасширениюUI"><span class="numhead-number">8.1.1. </span>Требования к Расширению UI</h3>'
           '<p><input type="text" name="variableValues.req_ui_ext_ai_desc" size="12" class="page-template-field" disabled=""/> '
           '<span class="templateparameter">(req_ui_ext_ai_desc)</span></p>')
assert body.count(OLD_811) == 1, "8.1.1 placeholder not found"
NEW_811 = ('<h3 id="DIT4ME-ТребованиякРасширениюUI"><span class="numhead-number">8.1.1. </span>'
           'Требования к Расширению UI</h3>' + chunk)
body = body.replace(OLD_811, NEW_811, 1)

# ---------------------------------------------------------------- 8.1.2: сводка 3 шаблонных правил (таблица)
def card(id_):
    return '<ac:link><ri:url ri:value="https://itsm.itsm-qa.mos.ru/automation_rules/%s" /></ac:link>' % id_

tpl_rules = [
    ("1", "10249331", "Закрыть запрос если переоткрыли", "on status update",
     "Защита от переоткрытия (повторного открытия) автоматически выполненного запроса. Если закрытый запрос снова переводят "
     "в работу, правило немедленно возвращает запрос в статус «Завершено» с прежними участником и причиной завершения "
     "и оставляет заявителю пояснение: запрос исполняется полностью автоматически, комментарии не учитываются, "
     "а для нового обращения нужно зарегистрировать отдельный запрос."),
    ("2", "10249443", "Создать запрос в Р-Сервис. Заказ демо-стенда (ApiGate 1.0)", "on status update",
     "Передаёт запрос в систему вендора (р-сервис) через интеграцию ApiGate 1.0. Когда запрос входит в статус "
     "«В рабочем процессе», правило собирает данные заявки (номер, список лиц, тему, описания, контактные данные, "
     "вложения и последний открытый комментарий) и вызывает вебхук «АТ. ApiGate 1.0 Передача в HPSM», который создаёт "
     "связанный запрос у вендора на заказ демо-стенда."),
    ("3", "13553013", "Завершить после решения от р-сервис", "on custom_fields update",
     "Завершает запрос после получения решения от вендора (р-сервис). Интеграция записывает результат в служебные поля "
     "расширения UI: note_rservice (заметка от вендора) и request_rservice (номер запроса вендора). Когда поле "
     "note_rservice обновляется при непустых обоих служебных полях и запрос ещё не завершён, правило завершает запрос "
     "и его рабочий процесс, добавляет в запрос комментарий с решением вендора и переносит исполнение на служебную "
     "учётную запись робота (команда «Jarvis»)."),
]
rows = ["<tr>", "<th><p>№</p></th>", "<th><p>ID</p></th>", "<th><p>Название</p></th>",
        "<th><p>Триггер</p></th>", "<th><p>Суть</p></th>", "<th><p>Ссылка на карточку</p></th>", "</tr>"]
for num, rid, rname, trig, essence in tpl_rules:
    rows += ["<tr>", "<td><p>%s</p></td>" % num, "<td><p>%s</p></td>" % rid,
             "<td><p>%s</p></td>" % esc(rname), "<td><p>%s</p></td>" % esc(trig),
             "<td><p>%s</p></td>" % essence, "<td>\n%s\n</td>" % card(rid), "</tr>"]
summary_table = ('<p>На шаблоне запроса настроено 3 правила автоматизации:</p>'
                 '<div class="table-wrap"><table class="wrapped confluenceTable"><tbody>\n'
                 + "\n".join(rows) + "\n</tbody></table></div>")

OLD_812 = ('<h3 id="DIT4ME-Требованиякправиламавтоматизации"><span class="numhead-number">8.1.2. </span>'
           '<span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3>'
           '<p><input type="text" name="variableValues.req_template_automation_rule_ai_description" size="12" class="page-template-field" disabled=""/> '
           '<span class="templateparameter">(req_template_automation_rule_ai_description)</span></p>')
assert body.count(OLD_812) == 1, "8.1.2 placeholder not found"
NEW_812 = ('<h3 id="DIT4ME-Требованиякправиламавтоматизации"><span class="numhead-number">8.1.2. </span>'
           '<span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3>' + summary_table)
body = body.replace(OLD_812, NEW_812, 1)

# ---------------------------------------------------------------- 8.2: Рабочий процесс
OLD_821 = ('<h3 id="DIT4ME-ТребованиякРасширениюUI.1"><span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3>'
           '<p><input type="text" name="variableValues.wf_ui_ext_desc" size="12" class="page-template-field" disabled=""/> '
           '<span class="templateparameter">(wf_ui_ext_desc)</span></p>')
assert body.count(OLD_821) == 1
NEW_821 = ('<h3 id="DIT4ME-ТребованиякРасширениюUI.1"><span class="numhead-number">8.2.1. </span>Требования к Расширению UI</h3>'
           '<p>Отсутствует (у РП %s нет своего UI-расширения)</p>' % WF_ID)
body = body.replace(OLD_821, NEW_821, 1)

OLD_822 = ('<h3 id="DIT4ME-Требованиякправиламавтоматизации.1"><span class="numhead-number">8.2.2. </span>'
           '<span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3>'
           '<p><input type="text" name="variableValues.wf_ar_desc" size="12" class="page-template-field" disabled=""/> '
           '<span class="templateparameter">(wf_ar_desc)</span></p>')
assert body.count(OLD_822) == 1
NEW_822 = ('<h3 id="DIT4ME-Требованиякправиламавтоматизации.1"><span class="numhead-number">8.2.2. </span>'
           '<span style="letter-spacing: 0.0px;">Требования к правилам автоматизации</span></h3>'
           '<p>Отсутствуют (у РП %s нет правил автоматизации)</p>' % WF_ID)
body = body.replace(OLD_822, NEW_822, 1)

# ---------------------------------------------------------------- 8.3: 4 подраздела «Шаблон задачи …»
def rule_block(rid, rname, trig, essence):
    return ('<h3 id="DIT4ME-Требованиякправилуавтоматизации-%s">Требования к правилу автоматизации %s - %s</h3>'
            '<p>%s</p>'
            '<p>Триггер: %s. Карточка правила: %s</p>'
            % (rid, rid, esc(rname), essence, esc(trig), card(rid)))

tasks = [
    ("4313", 'Мониторинг сбоев роботизации. Команда "ДИТ.MOS.ITSM.Администраторы"', [
        ("1914157", "Генерация задачи на обработку", "on status update",
         "Когда мониторинг назначен и в рабочем процессе есть провалившаяся задача, правило создаёт новую задачу "
         "«Обработка сбоев автоматизации (Автогенерация)» для ручного разбора инцидента: переносит в неё сведения о сбое "
         "(ссылку на сбойную задачу, комментарий от роботизации, фазу, инструкции), встраивает её в граф задач рабочего "
         "процесса (приёмник successors сбойной задачи) и отменяет остальные провалившиеся задачи, оставляя комментарий "
         "о генерации."),
        ("1914235", "Возврат статуса зарегистрировано", "on status update",
         "Не даёт задаче мониторинга выполняться раньше времени. Если задача мониторинга назначена, но среди её "
         "предшественников ещё остались задачи в статусе «Зарегистрировано» или провалившиеся задачи, правило возвращает "
         "задаче статус «Зарегистрировано» — работа по разбору сбоя не начинается, пока не обработаны предшествующие задачи."),
        ("1991869", "Автозавершение", "on status update",
         "Завершает задачу мониторинга, когда она больше не нужна: все провалившиеся задачи рабочего процесса обработаны "
         "и среди предшественников не осталось незавершённых работ. Если при этом задача мониторинга назначена или в работе, "
         "правило автоматически переводит её в статус «Завершено»."),
    ]),
    ("7411", "Балансировщик статусов", [
        ("2655131", "Завершить при назначении", "on status update",
         "Задача-заглушка нужна для корректной работы задачи сбоя «Мониторинг сбоев роботизации»: перед ней всегда должна "
         "быть задача в статусе, отличном от «Завершено» и «Отменена». Как только заглушку назначают, правило немедленно "
         "её завершает — этим состояние заглушки балансирует статусы предшественников в графе задач."),
    ]),
    ("31693", "Ожидание ответа сервиса. Предоставление доступа к демо стенду", [
        ("13934317", "Запуск таймера сбоя", "on status update",
         "Запускает контрольный таймер сбоя. Когда задачу ожидания назначают исполнителю-роботу (Служебная УЗ), правило "
         "рассчитывает момент отсрочки по рабочему календарю «Рабочие дни 9-18 для Согласования» и планирует отложенный "
         "запуск правила «Сбой обработки» — так включается контроль SLA вендора на автоматическую обработку запроса."),
        ("13934321", "Сбой обработки", "after delay",
         "Фиксирует сбой обработки. Правило запускается отложенно по таймеру, и если задача по-прежнему назначена роботу — "
         "значит, ответ от вендора (р-сервис) не поступил в срок. Тогда задача переводится в статус «Провалилась», "
         "а команде добавляется комментарий с номером связанного запроса, его темой, ссылками на открытые и завершённые "
         "запросы на стороне вендора и инструкциями по разбору инцидента."),
    ]),
    ("31697", "Авто-закрытие РП. Предоставление доступа к демо стенду", [
        ("13935097", "Проброс коммента в запрос, закрытие РП и запроса", "on status update",
         "Завершает весь запрос после сбоя и его ручного разбора. Когда задачу авто-закрытия назначают, правило добавляет "
         "в родительский запрос пояснение для заявителя (ошибки при обработке устранены, при отсутствии письма о "
         "предоставлении демо-стенда нужно подать новый запрос), завершает запрос и его рабочий процесс и переносит "
         "исполнение на служебную учётную запись робота (команда «Jarvis»)."),
    ]),
]

blocks = []
for tid, tname, rules in tasks:
    blocks.append('<h2 id="DIT4ME-Шаблонзадачи-%s">Шаблон задачи %s (ID %s)</h2>'
                  % (tid, esc(tname).replace('"', "&quot;"), tid))
    blocks.append('<p>Требования к Расширению UI: Отсутствует (у задачи нет расширения UI).</p>')
    for rid, rname, trig, essence in rules:
        blocks.append(rule_block(rid, rname, trig, essence))
NEW_83 = "".join(blocks)

# заменить блок 8.3 (от статического h2 до конца innerCell)
start = body.find('<h2 id="DIT4ME-Шаблонзадачи(task_template_name)">')
assert start != -1, "8.3 heading not found"
end = body.find('</div>', start)
assert end != -1
body = body[:start] + NEW_83 + '</div>' + body[end + len('</div>'):]

# ---------------------------------------------------------------- проверки
leftover = [x for x in ("variableValues.", "templateparameter", "template-variable?name=") if x in body]
assert not leftover, "unreplaced placeholders: %s" % leftover
raw_amp = [m.start() for m in re.finditer(r'&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;)', body)]
assert not raw_amp, "raw & at %s" % [body[max(0, p - 40):p + 20] for p in raw_amp[:3]]
try:
    ET.fromstring('<root xmlns:ac="https://ac" xmlns:ri="https://ri">' + body + "</root>")
    xml_ok = "OK"
except ET.ParseError as e:
    xml_ok = "FAIL: %s" % e
print("XML parse:", xml_ok)
assert xml_ok == "OK"
for phrase in [REQ_LINK, "RFC 8170964"]:
    assert phrase in body
n_href = body.count("<a href=")
ext_anchors = [m for m in re.finditer(r'<a href="(?!#)', body)]
print("a href total:", n_href, "| external (non-#):", len(ext_anchors))
assert n_href == 21 and len(ext_anchors) == 1, "anchors: 20 TOC + 1 RFC link"
_anchor_full = re.match(r'<a href="([^"]+)">([^<]+)</a>', body[ext_anchors[0].start():])
assert _anchor_full and _anchor_full.group(1) == RV["uri"] and _anchor_full.group(2) == "RFC %s" % RV["id"], \
    "req_uri anchor malformed: %s" % (_anchor_full.group(0)[:120] if _anchor_full else None)
n_link = body.count("<ac:link>")
print("ac:link count:", n_link)
assert n_link == 12, "expected 12 ac:link (10 rule cards + UI ext + workflow), got %d" % n_link
open("temp/page_body_8170964_v12.html", "w", encoding="utf-8").write(body)
print("body length:", len(body))

TITLE = "8170964-%s - Предоставление доступа к демо стенду (v1.2)" % TPL_SUBJ
payload = {
    "type": "page",
    "title": TITLE,
    "space": {"key": "DIT4ME"},
    "body": {"storage": {"value": body, "representation": "storage"}},
    "ancestors": [{"id": "735534111"}],
}
open("temp/payload_8170964_v12.json", "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False))
print("title:", TITLE)
print("OK")
