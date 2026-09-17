import pytest

from astro_core.profiles import (
    profile_to_filename,
    save_profile,
    load_profile,
    list_profiles,
    delete_profile,
)


# ============================================================
# Тесты преобразования имени в имя файла
# ============================================================

def test_profile_to_filename_basic():
    """Проверка базового преобразования имени в имя файла."""
    assert profile_to_filename("Иван") == "Иван.json"
    assert profile_to_filename("John Smith") == "John_Smith.json"


def test_profile_to_filename_special_chars():
    """Проверка удаления специальных символов."""
    assert profile_to_filename("Иван@2026!") == "Иван2026.json"
    assert profile_to_filename("test/profile") == "testprofile.json"


def test_profile_to_filename_empty():
    """Проверка обработки пустого или недопустимого имени."""
    assert profile_to_filename("") == "profile.json"
    assert profile_to_filename("@@@") == "profile.json"


def test_profile_to_filename_long():
    """Проверка ограничения длины имени файла."""
    long_name = "О" * 100
    filename = profile_to_filename(long_name)
    # 50 символов имени + ".json" (5 символов)
    assert len(filename) <= 55


def test_profile_to_filename_spaces():
    """Проверка замены пробелов на подчёркивания."""
    assert profile_to_filename("Иван  Петров") == "Иван_Петров.json"
    assert profile_to_filename("  spaces  ") == "spaces.json"


# ============================================================
# Тесты сохранения и загрузки
# ============================================================

def test_save_and_load_profile(tmp_path):
    """Проверка сохранения и загрузки профиля."""
    profile = {
        "name": "Тестовый",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }

    file_path = save_profile(profile, profiles_dir=tmp_path)
    assert file_path.exists()

    loaded = load_profile("Тестовый", profiles_dir=tmp_path)

    assert loaded["name"] == "Тестовый"
    assert loaded["date"] == "1990-05-15"
    assert loaded["time"] == "14:30"
    assert loaded["latitude"] == 55.7558
    assert loaded["longitude"] == 37.6173
    assert loaded["utc_offset_hours"] == 3
    assert "created_at" in loaded
    assert "updated_at" in loaded


def test_save_profile_missing_field(tmp_path):
    """Проверка, что сохранение без обязательного поля вызывает ошибку."""
    profile = {
        "name": "Неполный",
        "date": "1990-05-15",
        # Отсутствуют другие обязательные поля
    }

    with pytest.raises(ValueError):
        save_profile(profile, profiles_dir=tmp_path)


def test_load_profile_not_found(tmp_path):
    """Проверка, что загрузка несуществующего профиля вызывает ошибку."""
    with pytest.raises(FileNotFoundError):
        load_profile("Несуществующий", profiles_dir=tmp_path)


def test_save_profile_updates_timestamps(tmp_path):
    """Проверка, что при повторном сохранении обновляется updated_at."""
    profile = {
        "name": "Тест",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }

    # Первое сохранение
    save_profile(profile, profiles_dir=tmp_path)
    loaded_first = load_profile("Тест", profiles_dir=tmp_path)
    first_created = loaded_first["created_at"]

    # Повторное сохранение
    save_profile(profile, profiles_dir=tmp_path)
    loaded_second = load_profile("Тест", profiles_dir=tmp_path)

    # created_at должен сохраниться
    assert loaded_second["created_at"] == first_created
    # updated_at должен присутствовать
    assert "updated_at" in loaded_second


def test_save_profile_preserves_extra_fields(tmp_path):
    """Проверка, что дополнительные поля сохраняются."""
    profile = {
        "name": "СДополнением",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
        "timezone": "Europe/Moscow",
        "notes": "Важный комментарий",
    }

    save_profile(profile, profiles_dir=tmp_path)
    loaded = load_profile("СДополнением", profiles_dir=tmp_path)

    assert loaded["timezone"] == "Europe/Moscow"
    assert loaded["notes"] == "Важный комментарий"


# ============================================================
# Тесты списка профилей
# ============================================================

def test_list_profiles(tmp_path):
    """Проверка списка профилей."""
    # Создаём несколько профилей
    for name in ["Анна", "Борис", "Виктор"]:
        save_profile({
            "name": name,
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 55.7558,
            "longitude": 37.6173,
            "utc_offset_hours": 3,
        }, profiles_dir=tmp_path)

    profiles = list_profiles(profiles_dir=tmp_path)
    assert len(profiles) == 3

    # Проверяем сортировку по имени
    names = [p["name"] for p in profiles]
    assert names == sorted(names, key=str.lower)


def test_list_profiles_empty(tmp_path):
    """Проверка списка профилей в пустой папке."""
    profiles = list_profiles(profiles_dir=tmp_path)
    assert profiles == []


def test_list_profiles_nonexistent_dir(tmp_path):
    """Проверка списка профилей в несуществующей папке."""
    profiles = list_profiles(profiles_dir=tmp_path / "nonexistent")
    assert profiles == []


def test_list_profiles_skips_corrupted(tmp_path):
    """Проверка, что повреждённые файлы пропускаются."""
    # Создаём нормальный профиль
    save_profile({
        "name": "Нормальный",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }, profiles_dir=tmp_path)

    # Создаём повреждённый файл
    corrupted_path = tmp_path / "Повреждённый.json"
    corrupted_path.write_text("это не json {{{", encoding="utf-8")

    profiles = list_profiles(profiles_dir=tmp_path)
    assert len(profiles) == 1
    assert profiles[0]["name"] == "Нормальный"


# ============================================================
# Тесты удаления
# ============================================================

def test_delete_profile(tmp_path):
    """Проверка удаления профиля."""
    save_profile({
        "name": "ДляУдаления",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }, profiles_dir=tmp_path)

    # Первое удаление должно вернуть True
    assert delete_profile("ДляУдаления", profiles_dir=tmp_path) is True
    # Повторное удаление должно вернуть False
    assert delete_profile("ДляУдаления", profiles_dir=tmp_path) is False


def test_delete_nonexistent_profile(tmp_path):
    """Проверка удаления несуществующего профиля."""
    assert delete_profile("Несуществующий", profiles_dir=tmp_path) is False