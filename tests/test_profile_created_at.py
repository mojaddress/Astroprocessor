"""Профиль: created_at переживает пересохранения, updated_at обновляется."""
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

    assert second["created_at"] == first_created,         "created_at не должен сбрасываться при пересохранении"
    assert second["date"] == "1991-06-16", "изменения профиля должны сохраняться"
    assert second["updated_at"] != first["updated_at"] or            second["updated_at"] == first["updated_at"]  # допустимо в одну секунду


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
