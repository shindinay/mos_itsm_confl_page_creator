#!/usr/bin/env bash
# Публикация набора *.md в Confluence (itpm-wiki.mos.ru, пространство 4ME).
# Токен берётся из переменной окружения CONFLUENCE_API_KEY (значение не печатается).
# Использование:
#   ./publish.sh <каталог-или-файл> [--root-page ID]
# Примеры:
#   ./publish.sh ../pages
#   ./publish.sh ../pages --root-page 123456789
set -euo pipefail

# Git Bash переделывает аргумент "/" в путь Windows; отключаем это преобразование.
export MSYS_NO_PATHCONV=1
export MSYS2_ENV_CONV_EXCL="CONFLUENCE_PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_DIR="$(dirname "$SCRIPT_DIR")"
MD2CONF="$SCRIPT_DIR/venv/Scripts/md2conf"

# Токен лежит в ../.env (CONFLUENCE_API_KEY); значение не печатается.
ENV_FILE="$PROJ_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
fi

if [ ! -f "$MD2CONF" ]; then
    echo "ОШИБКА: md2conf не найден в $MD2CONF" >&2
    exit 1
fi
if [ -z "${CONFLUENCE_API_KEY:-}" ]; then
    echo "ОШИБКА: CONFLUENCE_API_KEY не задана. Файл $ENV_FILE не найден или пуст." >&2
    echo "Создайте файл .env в корне проекта со строкой: CONFLUENCE_API_KEY=\"ваш-токен\"" >&2
    exit 1
fi
if [ $# -lt 1 ]; then
    echo "ОШИБКА: укажите каталог или файл: ./publish.sh ../pages [--root-page ID]" >&2
    exit 1
fi

SRC="${1:-}"; shift || true
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$PROJ_DIR/output/publish-$STAMP.log"

echo "Публикация: $SRC"
echo "Журнал:     $LOG"

"$MD2CONF" \
    --domain itpm-wiki.mos.ru \
    --path / \
    --api-version v1 \
    --space 4ME \
    --no-overwrite \
    --webui-links \
    --no-notify \
    --no-generated-by \
    "$@" \
    "$SRC" 2>&1 | tee "$LOG"

echo ""
echo "Готово. Проверьте результат в браузере:"
echo "  https://itpm-wiki.mos.ru/spaces/4ME"
