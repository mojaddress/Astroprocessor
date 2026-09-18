"""
Модуль для работы с профилями рождения.

Профиль рождения — это сохранённый набор данных рождения:
имя, дата, время, координаты, смещение UTC и другие параметры.

Профили хранятся в папке `profiles/` как отдельные JSON-файлы.
Это обеспечивает простоту, прозрачность и надёжность хранения.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

# Папка для хранения профилей по умолчанию
DEFAULT_PROFILES_DIR = "profiles"

# Обязательные поля профиля
REQUIRED_PROFILE_FIELDS = [
    "name",
    "date",
    "time",
    "latitude",
    "longitude",
    "utc_offset_hours",
]


def get_profiles_dir(profiles_dir=None):
    """
    Возвращает путь к папке профилей как объект Path.

    Параметры:
        profiles_dir: пользовательский путь или None для пути по умолчанию

    Возвращает:
        Path к папке профилей
    """
    if profiles_dir is None:
        profiles_dir = DEFAULT_PROFILES_DIR
    return Path(profiles_dir)


def profile_to_filename(profile_name):
    """
    Преобразует имя профиля в безопасное имя файла.

    Правила:
        - Удаляются недопустимые символы (кроме букв, цифр, пробелов,
          дефисов и подчёркиваний).
        - Кириллица сохраняется (современные ОС её поддерживают).
        - Пробелы заменяются на подчёркивания.
        - Длина ограничивается 50 символами.
        - Если имя пустое, используется имя "profile".

    Параметры:
        profile_name: имя профиля

    Возвращает:
        строку имени файла с расширением .json
    """
    # Оставляем буквы, цифры, пробелы, дефисы и подчёркивания
    # (включая кириллицу благодаря re.UNICODE)
    safe = re.sub(r'[^\w\s\-]', '', profile_name, flags=re.UNICODE)

    # Убираем пробелы по краям и заменяем последовательности пробелов
    safe = safe.strip()
    safe = re.sub(r'\s+', '_', safe)

    # Ограничиваем длину
    safe = safe[:50]

    # Если получилось пусто, используем имя по умолчанию
    if not safe:
        safe = "profile"

    return safe + ".json"


def save_profile(profile_data, profiles_dir=None):
    """
    Сохраняет профиль рождения в файл.

    Параметры:
        profile_data: словарь с данными профиля
        profiles_dir: папка для хранения профилей

    Возвращает:
        Путь к сохранённому файлу (Path)

    Исключения:
        ValueError: если отсутствуют обязательные поля
    """
    # Проверяем обязательные поля
    for field in REQUIRED_PROFILE_FIELDS:
        if field not in profile_data:
            raise ValueError(f"Profile is missing required field: {field}")

    # Создаём папку, если её нет
    dir_path = get_profiles_dir(profiles_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    # Добавляем метаданные
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    profile_to_save = dict(profile_data)
    profile_to_save["updated_at"] = now

    if "created_at" not in profile_to_save:
        profile_to_save["created_at"] = now

    # Определяем имя файла по имени профиля
    filename = profile_to_filename(profile_data["name"])
    file_path = dir_path / filename

    # Сохраняем в JSON с поддержкой кириллицы
    file_path.write_text(
        json.dumps(profile_to_save, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return file_path


def load_profile(profile_name, profiles_dir=None):
    """
    Загружает профиль рождения из файла по имени профиля.

    Параметры:
        profile_name: имя профиля (как оно было сохранено)
        profiles_dir: папка для хранения профилей

    Возвращает:
        словарь с данными профиля

    Исключения:
        FileNotFoundError: если профиль не найден
    """
    dir_path = get_profiles_dir(profiles_dir)
    filename = profile_to_filename(profile_name)
    file_path = dir_path / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_name}")

    return json.loads(file_path.read_text(encoding="utf-8"))


def list_profiles(profiles_dir=None):
    """
    Возвращает список всех профилей в папке.

    Повреждённые файлы пропускаются без ошибки.

    Параметры:
        profiles_dir: папка для хранения профилей

    Возвращает:
        список словарей с данными профилей, отсортированных по имени
    """
    dir_path = get_profiles_dir(profiles_dir)

    if not dir_path.exists():
        return []

    profiles = []

    for file_path in sorted(dir_path.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))

            # Добавляем имя файла как служебное поле
            data["_filename"] = file_path.name
            profiles.append(data)

        except (json.JSONDecodeError, UnicodeDecodeError):
            # Пропускаем повреждённые файлы, чтобы один битый файл
            # не блокировал работу со всеми профилями
            continue

    # Сортируем по имени профиля (регистронезависимо)
    profiles.sort(key=lambda p: p.get("name", "").lower())

    return profiles


def delete_profile(profile_name, profiles_dir=None):
    """
    Удаляет профиль по имени.

    Параметры:
        profile_name: имя профиля
        profiles_dir: папка для хранения профилей

    Возвращает:
        True, если профиль был удалён, иначе False
    """
    dir_path = get_profiles_dir(profiles_dir)
    filename = profile_to_filename(profile_name)
    file_path = dir_path / filename

    if file_path.exists():
        file_path.unlink()
        return True

    return False