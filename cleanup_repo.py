"""Прекращение распространения лицензированных данных и персональных профилей.

Запуск:  py -3.11 cleanup_repo.py
Делает: .gitignore (артефакты сборки, профили, .kilo),
        profiles/README.md + profiles/example.json (безопасный шаблон),
        AstroProcessor.spec (эфемериды не пакуются по умолчанию).
Git-команды выполняет владелец отдельно - скрипт файлы только правит.
Идемпотентен: маркер ASTRO_CLEANUP_V1.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER = "ASTRO_CLEANUP_V1"

GITIGNORE_BLOCK = """
# --- ASTRO_CLEANUP_V1 ---
# Артефакты сборки: не хранятся в репозитории (в т.ч. установщик 60+ МБ)
build/
dist/
installer_output/
*.exe

# Персональные профили рождения: только локально.
# В репозитории - README и обезличенный пример.
profiles/*
!profiles/README.md
!profiles/example.json

# Служебные файлы инструментов разработки
.kilo/
"""

PROFILES_README = """# Профили рождения

Реальные профили (`*.json`) хранятся **только локально** и не попадают в репозиторий:
они содержат персональные данные (имя, дата, время, координаты рождения).

В репозитории лежит только `example.json` — обезличенный демонстрационный профиль.

## Как перенести профили на другой компьютер

1. Скопируйте файлы `*.json` из папки `profiles/` старого компьютера.
2. Положите их в папку `profiles/` нового компьютера.
3. Запустите программу — профили появятся в списке.

## Резервное копирование

Профили — пользовательские данные. Копируйте папку `profiles/` вместе с остальными
данными при резервировании. Удаление программы не должно удалять профили без спроса.
"""

EXAMPLE_PROFILE = """{
  "name": "Demo",
  "date": "1990-01-01",
  "time": "12:00",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "utc_offset_hours": 3.0,
  "timezone": "Europe/Moscow"
}
"""

SPEC_IMPORT_ANCHOR = "import sys"
SPEC_OLD_BLOCK = '''data_files = [
    # Ephemeris files
    ("ephe", "ephe"),
    # Cities database
    ("data/cities.json", "data"),
    # Settings template
    ("config/default_settings.json", "config"),
]'''
SPEC_NEW_BLOCK = '''# ASTRO_CLEANUP_V1: файлы эфемерид НЕ включаются в распространяемую сборку.
# Они лицензированы Astrodienst (AGPL-3.0 или коммерческая лицензия), поэтому
# публичный установщик не должен их содержать. Пользователь получает их отдельно
# (см. ephe/README.md). Для ЛИЧНОЙ сборки с данными: ASTRO_BUNDLE_EPHE=1.
BUNDLE_EPHE = os.environ.get("ASTRO_BUNDLE_EPHE", "0") == "1"

data_files = [
    # Cities database
    ("data/cities.json", "data"),
    # Settings template
    ("config/default_settings.json", "config"),
]

if BUNDLE_EPHE:
    data_files.append(("ephe", "ephe"))'''


def update_gitignore() -> None:
    path = ROOT / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if MARKER in text:
        print("[*] .gitignore уже содержит блок очистки.")
        return
    path.write_text(text.rstrip("\n") + "\n" + GITIGNORE_BLOCK, encoding="utf-8")
    print("[+] .gitignore: артефакты сборки, профили, .kilo исключены.")


def create_profiles_docs() -> None:
    folder = ROOT / "profiles"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README.md").write_text(PROFILES_README, encoding="utf-8")
    example = folder / "example.json"
    if not example.exists():
        example.write_text(EXAMPLE_PROFILE, encoding="utf-8")
    print("[+] profiles/README.md и profiles/example.json готовы.")


def patch_spec() -> None:
    path = ROOT / "AstroProcessor.spec"
    if not path.exists():
        print("[!] AstroProcessor.spec не найден - пропуск.")
        return
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("[*] AstroProcessor.spec уже пропатчен.")
        return
    if SPEC_OLD_BLOCK not in src or SPEC_IMPORT_ANCHOR not in src:
        print("[X] Якоря в .spec не найдены. Файл НЕ изменён - сообщите агенту.")
        sys.exit(1)
    src = src.replace(SPEC_IMPORT_ANCHOR, SPEC_IMPORT_ANCHOR + "\nimport os", 1)
    src = src.replace(SPEC_OLD_BLOCK, SPEC_NEW_BLOCK, 1)
    try:
        compile(src, str(path), "exec")
    except SyntaxError as exc:
        print(f"[X] SyntaxError в .spec после правки: {exc}. Файл НЕ изменён.")
        sys.exit(1)
    shutil.copy2(path, path.with_name(path.name + ".bak_cleanup"))
    path.write_text(src, encoding="utf-8")
    print("[+] AstroProcessor.spec: эфемериды больше не пакуются по умолчанию.")


def main() -> None:
    update_gitignore()
    create_profiles_docs()
    patch_spec()
    print("=" * 70)
    print("Файлы подготовлены. Далее - git-команды из инструкции (по порядку).")
    print("ВАЖНО: перед filter-repo вывод git status --porcelain должен быть пустым.")


if __name__ == "__main__":
    main()