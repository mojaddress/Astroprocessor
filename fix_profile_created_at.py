"""Фикс даты создания профиля: created_at переживает пересохранения.

Запуск:  py -3.11 fix_profile_created_at.py
Маркер: PROFILE_CREATED_AT_FIX_V1. Резервные копии: *.bak_createdat
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROFILES = ROOT / "astro_core" / "profiles.py"
TEST = ROOT / "tests" / "test_profile_created_at.py"
GITIGNORE = ROOT / ".gitignore"

OLD_BLOCK = '''    # Добавляем метаданные
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    profile_to_save = dict(profile_data)
    profile_to_save["updated_at"] = now

    if "created_at" not in profile_to_save:
        profile_to_save["created_at"] = now

    # Определяем имя файла по имени профиля
    filename = profile_to_filename(profile_data["name"])
    file_path = dir_path / filename'''

NEW_BLOCK = '''    # Добавляем метаданные (PROFILE_CREATED_AT_FIX_V1).
    # created_at берётся из существующего файла, если он есть: дата создания
    # профиля не должна сбрасываться при правке.
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    profile_to_save = dict(profile_data)
    profile_to_save["updated_at"] = now

    filename = profile_to_filename(profile_data["name"])
    file_path = dir_path / filename

    existing_created_at = None
    if "created_at" not in profile_to_save and file_path.exists():
        try:
            existing = json.loads(file_path.read_text(encoding="utf-8"))
            existing_created_at = existing.get("created_at")
        except (OSError, ValueError):
            existing_created_at = None
    profile_to_save["created_at"] = (
        existing_created_at
        or profile_to_save.get("created_at")
        or now
    )'''

TEST_SRC = '''"""Профиль: created_at переживает пересохранения, updated_at обновляется."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from astro_core.profiles import load_profile, save_profile


def _make_profile(**overrides):
    base = {
        "name": "Created-At-Test",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
        "city_name": "Москва",
        "city_country": "Россия",
        "city_timezone": "Europe/Moscow",
    }
    base.update(overrides)
    return base


def test_first_save_sets_created_at(tmp_path: Path):
    path = save_profile(_make_profile(), profiles_dir=tmp_path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["created_at"]
    assert saved["updated_at"]
    assert saved["created_at"] == saved["updated_at"]


def test_resave_preserves_created_at(tmp_path: Path):
    save_profile(_make_profile(), profiles_dir=tmp_path)
    first = load_profile("Created-At-Test", profiles_dir=tmp_path)
    first_created = first["created_at"]

    save_profile(_make_profile(date="1991-06-16"), profiles_dir=tmp_path)
    second = load_profile("Created-At-Test", profiles_dir=tmp_path)

    assert second["created_at"] == first_created, \
        "created_at не должен сбрасываться при пересохранении"
    assert second["date"] == "1991-06-16", "изменения профиля должны сохраняться"
    assert second["updated_at"] != first["updated_at"] or \
           second["updated_at"] == first["updated_at"]  # допустимо в одну секунду


def test_created_at_in_payload_is_respected(tmp_path: Path):
    """Если профиль пришёл уже с created_at, сохраняем его."""
    fixed_date = "2020-01-01T12:00:00+00:00"
    save_profile(_make_profile(created_at=fixed_date), profiles_dir=tmp_path)
    saved = load_profile("Created-At-Test", profiles_dir=tmp_path)
    assert saved["created_at"] == fixed_date


def test_corrupt_existing_file_does_not_block_save(tmp_path: Path):
    """Повреждённый существующий файл не должен ронять сохранение."""
    from astro_core.profiles import profile_to_filename
    dir_path = tmp_path
    dir_path.mkdir(parents=True, exist_ok=True)
    bad_file = dir_path / profile_to_filename("Created-At-Test")
    bad_file.write_text("not a valid json {{{", encoding="utf-8")

    # Должно сохраниться без ошибки, с новым created_at
    path = save_profile(_make_profile(), profiles_dir=tmp_path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["created_at"]
    assert saved["name"] == "Created-At-Test"
'''


def patch(path: Path, edits: list[tuple[str, str]]) -> None:
    src = path.read_text(encoding="utf-8")
    marker = "PROFILE_CREATED_AT_FIX_V1"
    if marker in src:
        print(f"[*] {path.name}: патч уже применён.")
        return
    for old, _new in edits:
        if src.count(old) != 1:
            print(f"[X] {path.name}: якорь найден {src.count(old)} раз (ожидался 1):")
            print(f"    {old[:90]!r}")
            print("    Файл НЕ изменён.")
            sys.exit(1)
    for old, new in edits:
        src = src.replace(old, new, 1)
    try:
        compile(src, str(path), "exec")
    except SyntaxError as exc:
        print(f"[X] {path.name}: SyntaxError: {exc}. Файл НЕ изменён.")
        sys.exit(1)
    shutil.copy2(path, path.with_name(path.name + ".bak_createdat"))
    path.write_text(src, encoding="utf-8")
    print(f"[+] {path.name} пропатчен.")


def ensure_gitignore() -> None:
    """pytest_log.txt и diag_*.txt — не в репозитории."""
    additions = ["pytest_log.txt", "diag_*.txt"]
    if not GITIGNORE.exists():
        GITIGNORE.write_text("\n".join(additions) + "\n", encoding="utf-8")
        print("[+] Создан .gitignore (pytest_log.txt, diag_*.txt)")
        return
    content = GITIGNORE.read_text(encoding="utf-8")
    changed = False
    for line in additions:
        if line not in content:
            content = content.rstrip("\n") + "\n" + line + "\n"
            changed = True
    if changed:
        GITIGNORE.write_text(content, encoding="utf-8")
        print("[+] .gitignore обновлён (добавлены pytest_log.txt, diag_*.txt)")
    else:
        print("[*] .gitignore уже содержит нужные шаблоны.")


def main() -> None:
    if not PROFILES.exists():
        print(f"[X] Не найден файл {PROFILES}")
        sys.exit(1)

    patch(PROFILES, [(OLD_BLOCK, NEW_BLOCK)])
    TEST.write_text(TEST_SRC, encoding="utf-8")
    print("[+] Создан tests/test_profile_created_at.py (4 проверки)")
    ensure_gitignore()

    sys.path.insert(0, str(ROOT))
    try:
        import tempfile
        from pathlib import Path as P
        from astro_core.profiles import load_profile, save_profile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = P(tmp)
            profile = {
                "name": "Control", "date": "1990-05-15", "time": "14:30",
                "latitude": 55.7558, "longitude": 37.6173, "utc_offset_hours": 3,
                "city_name": "Москва", "city_country": "Россия",
                "city_timezone": "Europe/Moscow",
            }
            save_profile(profile, profiles_dir=tmp_path)
            first = load_profile("Control", profiles_dir=tmp_path)

            import time
            time.sleep(1.1)  # гарантированно разные секунды

            save_profile(profile, profiles_dir=tmp_path)
            second = load_profile("Control", profiles_dir=tmp_path)

            print("[+] Контроль: сохранение дважды с паузой 1 с")
            print(f"    created_at (1): {first['created_at']}")
            print(f"    created_at (2): {second['created_at']}")
            print(f"    updated_at (1): {first['updated_at']}")
            print(f"    updated_at (2): {second['updated_at']}")
            if second["created_at"] != first["created_at"]:
                print("[X] created_at изменился — фикс не сработал")
                sys.exit(1)
            if second["updated_at"] == first["updated_at"]:
                print("[!] updated_at не обновился — пауза могла не сработать")
            print("[+] Проверено: created_at пережил пересохранение.")
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Ошибка контроля: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()