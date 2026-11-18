"""Упаковка: hidden import swisseph (не pyswisseph) + верификация сборки.

Запуск:  py -3.11 fix_packaging.py
Патчит:  AstroProcessor.spec (PACKAGING_FIX_V1)
Пересоздаёт: make_release.py (--noconfirm, пост-проверка swisseph в dist)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "AstroProcessor.spec"
RELEASE = ROOT / "make_release.py"

RELEASE_SRC = '''"""Локальный релизный цикл: тесты -> эфемериды -> сборка -> верификация.

Запуск:  py -3.11 make_release.py
         py -3.11 make_release.py --with-ephe   ТОЛЬКО личное использование
Сборка по умолчанию НЕ включает лицензированные файлы Swiss Ephemeris.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd):
    print(">", " ".join(str(part) for part in cmd))
    return subprocess.run([str(part) for part in cmd], cwd=ROOT)


def find_swisseph(dist: Path):
    return [p for p in dist.rglob("*")
            if p.is_file() and p.name.lower().startswith("swisseph")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Релизный цикл Astro Processor")
    parser.add_argument("--with-ephe", action="store_true",
                        help="включить эфемериды в сборку (ТОЛЬКО лично)")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if not args.skip_tests:
        result = run([sys.executable, "-m", "pytest", "tests", "-q"])
        if result.returncode != 0:
            print("[X] Тесты не прошли - релиз остановлен.")
            return 1

    run([sys.executable, "fetch_ephe.py", "--check"])

    env = dict(os.environ)
    env["ASTRO_BUNDLE_EPHE"] = "1" if args.with_ephe else "0"
    if args.with_ephe:
        print("[!] ВНИМАНИЕ: сборка с эфемеридами допустима только лично.")
    result = run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
                  "AstroProcessor.spec"])
    if result.returncode != 0:
        print("[X] PyInstaller завершился с ошибкой.")
        return 1

    dist = ROOT / "dist" / "AstroProcessor"
    if not dist.exists():
        print("[X] Папка dist/AstroProcessor не создана.")
        return 1

    # PACKAGING_FIX_V1: без swisseph собранное приложение молча деградирует.
    found = find_swisseph(dist)
    if not found:
        print("[X] В сборке НЕТ модуля swisseph - приложение деградирует до Moshier.")
        print("    Проверьте hidden_imports в AstroProcessor.spec.")
        return 1
    print(f"[+] swisseph в сборке: {found[0].relative_to(dist)}")

    iscc = (Path(os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)"))
            / "Inno Setup 6" / "ISCC.exe")
    if iscc.exists():
        run([iscc, "AstroProcessor.iss"])
    else:
        print("[i] Inno Setup не найден - инсталлятор пропущен, portable готов.")

    print("=" * 70)
    print(f"Portable: {dist}")
    print("Чек-лист перед публикацией:")
    print("  [ ] ASTRO_BUNDLE_EPHE=0 для публичного артефакта")
    print("  [ ] тесты зелёные")
    print("  [ ] LICENSES.md отражает состав поставки")
    print("  [ ] версия обновлена в AstroProcessor.spec / .iss")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def main() -> None:
    if not SPEC.exists():
        print(f"[X] Не найден файл {SPEC}")
        sys.exit(1)

    src = SPEC.read_text(encoding="utf-8")
    if "PACKAGING_FIX_V1" in src:
        print("[*] AstroProcessor.spec: патч уже применён.")
    else:
        anchor = '    "pyswisseph",\n'
        if src.count(anchor) != 1:
            print(f"[X] Якорь hidden import найден {src.count(anchor)} раз. Файл НЕ изменён.")
            sys.exit(1)
        src = src.replace(
            anchor,
            '    "swisseph",  # PACKAGING_FIX_V1: импортируемый модуль - swisseph,\n'
            '    # а имя pip-пакета pyswisseph; прежнее имя не находилось и сборка\n'
            '    # молча оставалась без эфемерид.\n', 1)
        try:
            compile(src, str(SPEC), "exec")
        except SyntaxError as exc:
            print(f"[X] SyntaxError в spec: {exc}. Файл НЕ изменён.")
            sys.exit(1)
        shutil.copy2(SPEC, SPEC.with_name(SPEC.name + ".bak_packaging"))
        SPEC.write_text(src, encoding="utf-8")
        print("[+] AstroProcessor.spec: hidden import исправлен на swisseph.")

    RELEASE.write_text(RELEASE_SRC, encoding="utf-8")
    print("[+] make_release.py пересоздан (--noconfirm, пост-проверка swisseph).")


if __name__ == "__main__":
    main()