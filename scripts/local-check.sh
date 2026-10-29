#!/usr/bin/env bash
# Локальная проверка конвертации *.md в формат Confluence (без записи на сервер).
# Использование: ./local-check.sh [каталог-с-*.md]   (по умолчанию ../pages)
# Результат: .csf-файлы и ассеты в ../temp/local-check/<метка времени>
set -euo pipefail

# Git Bash переделывает аргумент "/" в путь Windows; отключаем это преобразование.
export MSYS_NO_PATHCONV=1
export MSYS2_ENV_CONV_EXCL="CONFLUENCE_PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="${1:-$PROJ_DIR/pages}"
MD2CONF="$SCRIPT_DIR/venv/Scripts/md2conf"

if [ ! -f "$MD2CONF" ]; then
    echo "ОШИБКА: md2conf не найден в $MD2CONF — сначала установите venv (см. manifesto/README.md)" >&2
    exit 1
fi
if [ ! -e "$SRC_DIR" ]; then
    echo "ОШИБКА: каталог с файлами не найден: $SRC_DIR" >&2
    exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
WORK_DIR="$PROJ_DIR/temp/local-check/$STAMP"
mkdir -p "$WORK_DIR"
if [ -f "$SRC_DIR" ]; then
    cp "$SRC_DIR" "$WORK_DIR/"
else
    cp -r "$SRC_DIR/." "$WORK_DIR/"
fi

echo "Источник:      $SRC_DIR"
echo "Рабочая копия: $WORK_DIR"
echo "Проверка идёт (на сервер ничего не пишется)..."

# Python под Windows не понимает пути вида /d/... — переводим в D:\...
WORK_DIR_WIN="$(cygpath -w "$WORK_DIR")"

"$MD2CONF" --local --domain itpm-wiki.mos.ru --path / --space 4ME --no-notify --no-generated-by "$WORK_DIR_WIN"

echo ""
echo "Готово. Сгенерированные файлы формата Confluence (.csf):"
find "$WORK_DIR" -name "*.csf" -print | sed "s|$WORK_DIR/||"
echo ""
echo "Просмотрите .csf-файлы: это то, как страницы будут выглядеть на сервере."
echo "Каталог $WORK_DIR можно удалить в любой момент."
