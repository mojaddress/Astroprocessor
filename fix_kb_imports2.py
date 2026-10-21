"""Надёжное добавление импорта pyqtSignal с учётом многострочных импортов (P-13)."""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

FILES = (
    "ui_qt/widgets/transits_panel.py",
    "ui_qt/widgets/interpretation_panel.py",
    "ui_qt/widgets/synastry_panel.py",
)


def fix_file(p):
    with open(p, encoding="utf-8") as f:
        src = f.read()
    head = src.split("\nclass ")[0]
    if "pyqtSignal" in head:
        print(f"OK: {p} — pyqtSignal уже импортирован, пропуск")
        return

    lines = src.split("\n")

    # 1) Если есть строка from PyQt6.QtCore import X — добавляем pyqtSignal к ней
    for i, l in enumerate(lines):
        m = re.match(r"^from PyQt6\.QtCore import (.+)$", l)
        if m and not l.strip().endswith("("):
            names = [n.strip() for n in m.group(1).split(",")]
            if "pyqtSignal" not in names:
                names.append("pyqtSignal")
                lines[i] = f"from PyQt6.QtCore import {', '.join(names)}"
                src = "\n".join(lines)
                compile(src, p, "exec")  # P-2: компиляция до записи
                with open(p, "w", encoding="utf-8") as f:
                    f.write(src)
                print(f"OK: {p} — pyqtSignal добавлен к существующей строке QtCore")
                return

    # 2) Иначе ищем конец последнего PyQt6-блока (однострочного или многострочного)
    last_pyqt6_end = -1
    i = 0
    while i < len(lines):
        l = lines[i]
        if re.match(r"^from PyQt6\.", l):
            if "(" in l and ")" not in l:
                # многострочный импорт — ищем закрывающую )
                j = i + 1
                while j < len(lines) and ")" not in lines[j]:
                    j += 1
                last_pyqt6_end = j
                i = j + 1
                continue
            else:
                last_pyqt6_end = i
        i += 1

    if last_pyqt6_end < 0:
        print(f"ОШИБКА: {p} — не найден ни один PyQt6-импорт для привязки")
        return

    new_lines = (lines[:last_pyqt6_end + 1]
                 + ["from PyQt6.QtCore import pyqtSignal"]
                 + lines[last_pyqt6_end + 1:])
    src = "\n".join(new_lines)
    compile(src, p, "exec")  # P-2: компиляция до записи
    with open(p, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"OK: {p} — импорт pyqtSignal добавлен после строки {last_pyqt6_end + 1}")


for rel in FILES:
    fix_file(os.path.join(ROOT, rel))

print("\nГОТОВО. Запускайте тесты и приложение.")