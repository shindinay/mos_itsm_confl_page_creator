# -*- coding: utf-8 -*-
"""Трансформирует устаревший CSS-макет ITSM-шаблона Confluence в plain HTML.

ITSM-шаблоны хранят контент в формате:
  <div class="contentLayout2">
    <div class="columnLayout single" data-layout="single">
      <div class="cell normal" data-type="normal">
        <div class="innerCell">секция 1</div>
      </div>
    </div>
    <div class="columnLayout single" data-layout="single">
      <div class="cell normal" data-type="normal">
        <div class="innerCell">секция 2</div>
      </div>
    </div>
    ...
  </div>

Каждая innerCell содержит контент одной секции.
Последний </div> внутри каждой секции относится к структуре columnLayout,
а не к контенту — его нужно удалить.

Использование:
  python transform_legacy_layout.py --input <page_body.html> [--out <output.html>]
"""
import argparse
import os
import re


def transform(html):
    """Извлекает контент из innerCell и убирает лишние </div>."""
    # Найти contentLayout2
    cl2_re = re.compile(r'<div\s+class="contentLayout2"[^>]*>', re.I)
    cl2_m = cl2_re.search(html)
    if not cl2_m:
        print('contentLayout2 не найден — файл не трансформирован.')
        return html

    # Определить границы contentLayout2
    depth = 1
    pos = html.find('>', cl2_m.start()) + 1
    open_div_re = re.compile(r'<div\b[^>]*>', re.I)
    close_div_re = re.compile(r'</div\s*>', re.I)

    while pos < len(html):
        no = open_div_re.search(html, pos)
        nc = close_div_re.search(html, pos)
        if nc is None:
            break
        if no and no.start() < nc.start():
            depth += 1
            pos = no.end()
        else:
            pos = nc.end()
            depth -= 1
            if depth == 0:
                block_end = pos
                break

    cl2_content = html[:block_end]

    # Извлечь контент из каждой innerCell
    inner_re = re.compile(r'<div\s+class="innerCell"[^>]*>', re.I)
    sections = []
    for m in inner_re.finditer(cl2_content):
        pos = m.end()
        depth = 1
        end = None

        while pos < len(cl2_content):
            no = open_div_re.search(cl2_content, pos)
            nc = close_div_re.search(cl2_content, pos)
            if nc is None:
                break
            if no and no.start() < nc.start():
                depth += 1
                pos = no.end()
            else:
                pos = nc.end()
                depth -= 1
                if depth == 0:
                    end = pos
                    break

        if end:
            content = cl2_content[m.end():end].strip()
            # Убрать последний </div> — он принадлежит columnLayout
            last_close = list(close_div_re.finditer(content))
            if last_close:
                content = content[:last_close[-1].start()].strip()
            sections.append(content)

    if not sections:
        print('Секции не найдены.')
        return html

    # Объединить секции — plain HTML (без ac:layout, без обёртки)
    return '\n'.join(sections)


def main():
    parser = argparse.ArgumentParser(
        description='Трансформирует legacy ITSM layout в plain HTML'
    )
    parser.add_argument(
        '--input', required=True,
        help='Путь к HTML-файлу с legacy-макетом'
    )
    parser.add_argument(
        '--out', default=None,
        help='Путь для результата (по умолчанию — перезаписать input)'
    )
    args = parser.parse_args()

    input_path = args.input
    output_path = args.out if args.out else input_path

    with open(input_path, 'r', encoding='utf-8') as f:
        old_body = f.read()

    print(f'Входной файл: {input_path} ({len(old_body)} байт)')

    has_legacy = (
        'columnLayout' in old_body
        or 'contentLayout2' in old_body
        or 'innerCell' in old_body
    )

    if not has_legacy:
        print('Legacy-макет не найден — файл не нужен трансформации.')
        return

    new_body = transform(old_body)
    print(f'Выходной файл: {output_path} ({len(new_body)} байт)')

    backup_path = input_path + '.backup'
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(input_path, backup_path)
        print(f'Бэкап создан: {backup_path}')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_body)
    print('Готово.')

    # Верификация баланса тегов
    open_div = len(re.findall(r'<div\b[^>]*>', new_body, re.I))
    close_div = len(re.findall(r'</div\s*>', new_body, re.I))
    open_p = len(re.findall(r'<p\b', new_body, re.I))
    close_p = len(re.findall(r'</p\s*>', new_body, re.I))
    open_span = len(re.findall(r'<span\b', new_body, re.I))
    close_span = len(re.findall(r'</span\s*>', new_body, re.I))

    print(f'Divs: {open_div} open, {close_div} close, balanced={open_div == close_div}')
    print(f'<p> tags: {open_p} open, {close_p} close, balanced={open_p == close_p}')
    print(f'<span> tags: {open_span} open, {close_span} close, balanced={open_span == close_span}')
