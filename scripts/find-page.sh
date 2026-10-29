#!/usr/bin/env bash
# Найти страницу Confluence по названию (или показать список пространств).
# Токен берётся из переменной окружения CONFLUENCE_API_KEY (значение не печатается).
# Использование:
#   ./find-page.sh "название страницы"        — поиск страниц по названию
#   ./find-page.sh --spaces                   — список пространств
set -euo pipefail

# Токен лежит в ../.env (CONFLUENCE_API_KEY); значение не печатается.
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
fi

DOMAIN="itpm-wiki.mos.ru"
BASE="https://$DOMAIN"

if [ -z "${CONFLUENCE_API_KEY:-}" ]; then
    echo "ОШИБКА: CONFLUENCE_API_KEY не задана. Файл $ENV_FILE не найден или пуст." >&2
    echo "Создайте файл .env в корне проекта со строкой: CONFLUENCE_API_KEY=\"ваш-токен\"" >&2
    exit 1
fi

if [ "${1:-}" = "--spaces" ]; then
    curl -sS -f -H "Authorization: Bearer $CONFLUENCE_API_KEY" \
        "$BASE/rest/api/space?limit=50" | python -c \
        "import json,sys; d=json.load(sys.stdin); [print(r['key'], '-', r['name']) for r in d['results']]"
    exit 0
fi

QUERY="${1:-}"
if [ -z "$QUERY" ]; then
    echo "ОШИБКА: укажите название страницы или --spaces" >&2
    exit 1
fi

CQL="type=page AND title~\"$QUERY\""
# Git Bash кодирует русские буквы в CP1251; сервер ждёт UTF-8, поэтому
# запрос кодируем в UTF-8 сами через Python.
python - "$QUERY" "$BASE" "$CONFLUENCE_API_KEY" <<'PYEOF'
import json, sys, urllib.parse, urllib.request

query, base, token = sys.argv[1], sys.argv[2], sys.argv[3]
cql = f'type=page AND title~"{query}"'
url = base + "/rest/api/content/search?" + urllib.parse.urlencode({"cql": cql, "limit": "15"})
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)
for r in data.get("results", []):
    print(r["id"], "-", r["title"])
if not data.get("results"):
    print("Ничего не найдено.")
PYEOF
