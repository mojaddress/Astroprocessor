"""
Расширенные тесты для модуля профилей.

Проверяют:
- сохранение и загрузку профиля;
- редактирование профиля;
- переименование профиля;
- удаление профиля.
"""

import pytest

from astro_core.profiles import (
    save_profile,
    load_profile,
    list_profiles,
    delete_profile,
)


def test_save_and_load_profile(tmp_path):
    """Проверка сохранения и загрузки профиля."""
    profile = {
        "name": "Тестовый",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
        "city": "Москва",
        "timezone": "Europe/Moscow",
    }

    save_profile(profile, profiles_dir=tmp_path)
    loaded = load_profile("Тестовый", profiles_dir=tmp_path)

    assert loaded["name"] == "Тестовый"
    assert loaded["date"] == "1990-05-15"
    assert loaded["city"] == "Москва"
    assert loaded["timezone"] == "Europe/Moscow"


def test_edit_profile(tmp_path):
    """Проверка редактирования профиля (перезапись с тем же именем)."""
    profile = {
        "name": "Тестовый",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }

    save_profile(profile, profiles_dir=tmp_path)

    # Редактируем профиль (меняем время)
    edited_profile = dict(profile)
    edited_profile["time"] = "15:00"
    save_profile(edited_profile, profiles_dir=tmp_path)

    loaded = load_profile("Тестовый", profiles_dir=tmp_path)
    assert loaded["time"] == "15:00"


def test_rename_profile(tmp_path):
    """Проверка переименования профиля."""
    profile = {
        "name": "СтароеИмя",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }

    save_profile(profile, profiles_dir=tmp_path)

    # Переименовываем: сохраняем с новым именем, удаляем старое
    renamed_profile = dict(profile)
    renamed_profile["name"] = "НовоеИмя"
    save_profile(renamed_profile, profiles_dir=tmp_path)
    delete_profile("СтароеИмя", profiles_dir=tmp_path)

    # Старый профиль должен быть удалён
    with pytest.raises(FileNotFoundError):
        load_profile("СтароеИмя", profiles_dir=tmp_path)

    # Новый профиль должен существовать
    loaded = load_profile("НовоеИмя", profiles_dir=tmp_path)
    assert loaded["name"] == "НовоеИмя"


def test_delete_profile(tmp_path):
    """Проверка удаления профиля."""
    profile = {
        "name": "ДляУдаления",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }

    save_profile(profile, profiles_dir=tmp_path)
    assert delete_profile("ДляУдаления", profiles_dir=tmp_path) is True
    assert delete_profile("ДляУдаления", profiles_dir=tmp_path) is False