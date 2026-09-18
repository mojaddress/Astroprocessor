"""
Модуль для работы с базой городов.

Предоставляет функции:
- загрузка базы городов из файла;
- поиск города по названию;
- получение города по точному названию;
- получение списка всех городов для выбора.

База городов хранится в файле data/cities.json.
"""

import json
from pathlib import Path

# Путь к файлу базы городов
# Файл находится в папке data/ в корне проекта
CITIES_FILE = Path(__file__).parent.parent / "data" / "cities.json"

# Кэш загруженных городов для избежания повторной загрузки
_cities_cache = None


def load_cities():
    """
    Загружает базу городов из файла.

    Результат кэшируется, чтобы не читать файл при каждом вызове.

    Возвращает:
        список словарей с данными городов
    """
    global _cities_cache

    if _cities_cache is not None:
        return _cities_cache

    if not CITIES_FILE.exists():
        return []

    try:
        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            _cities_cache = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Если файл повреждён, возвращаем пустой список
        _cities_cache = []

    return _cities_cache


def search_cities(query, limit=20):
    """
    Ищет города по названию (на русском или английском).

    Поиск работает по принципу:
    1. Сначала города, название которых начинается с запроса.
    2. Затем города, название которых содержит запрос.

    Параметры:
        query: строка поиска
        limit: максимальное количество результатов

    Возвращает:
        список словарей с данными городов
    """
    cities = load_cities()

    if not query or not query.strip():
        return cities[:limit]

    query_lower = query.lower().strip()

    # Разделяем результаты на две группы:
    # 1. Названия, начинающиеся с запроса (более релевантные)
    # 2. Названия, содержащие запрос (менее релевантные)
    starts_with = []
    contains = []

    for city in cities:
        name_lower = city.get("name", "").lower()
        name_en_lower = city.get("name_en", "").lower()
        country_lower = city.get("country", "").lower()

        # Проверяем совпадение с названием города или страны
        if name_lower.startswith(query_lower) or name_en_lower.startswith(query_lower):
            starts_with.append(city)
        elif query_lower in name_lower or query_lower in name_en_lower or query_lower in country_lower:
            contains.append(city)

    # Объединяем результаты: сначала более релевантные
    results = starts_with + contains

    return results[:limit]


def get_city_by_name(name):
    """
    Возвращает город по точному названию.

    Параметры:
        name: точное название города

    Возвращает:
        словарь с данными города или None, если город не найден
    """
    cities = load_cities()

    for city in cities:
        if city.get("name") == name:
            return city

    return None


def get_all_city_names():
    """
    Возвращает список всех названий городов для выбора.

    Список отсортирован по алфавиту.

    Возвращает:
        список названий городов
    """
    cities = load_cities()
    names = [city.get("name", "") for city in cities if city.get("name")]
    return sorted(names)


def get_city_display_name(city):
    """
    Возвращает отображаемое имя города для интерфейса.

    Формат: "Название (Страна)"

    Параметры:
        city: словарь с данными города

    Возвращает:
        строку для отображения
    """
    name = city.get("name", "")
    country = city.get("country", "")

    if country:
        return f"{name} ({country})"
    return name