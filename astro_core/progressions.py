"""
Модуль для расчёта прогрессий.

Поддерживает:
- Вторичные прогрессии (день за год)
- Прогрессии солнечной дуги

Вторичные прогрессии:
    Принцип: 1 день после рождения = 1 год жизни.
    Чтобы узнать прогрессивную карту на возраст N лет,
    строим карту на N дней после рождения.

Прогрессии солнечной дуги:
    Принцип: все натальные планеты продвигаются на то же расстояние,
    что и прогрессивное Солнце.
"""

from datetime import datetime, timedelta

from .chart import build_natal_chart
from .constants import DEFAULT_SETTINGS
from .time_service import parse_local_datetime, datetime_to_jd
from .utils import normalize_longitude, sign_from_longitude
from .aspects import calculate_aspects


def calculate_secondary_progressions(birth, progression_date, settings=None):
    """
    Рассчитывает вторичные прогрессии (день за год).

    Принцип: 1 день после рождения = 1 год жизни.
    Чтобы узнать прогрессивную карту на возраст N лет,
    строим карту на N дней после рождения.

    Параметры:
        birth: данные рождения (словарь с полями:
               name, date, time, latitude, longitude, utc_offset_hours)
        progression_date: дата прогрессии (строка "ГГГГ-ММ-ДД")
        settings: настройки расчёта

    Возвращает:
        словарь с прогрессивной картой:
        - birth: данные рождения
        - progression_date: дата прогрессии
        - age_days: возраст в днях (разница между датой прогрессии и датой рождения)
        - age_years: возраст в годах
        - progressed_birth: данные для расчёта прогрессивной карты
        - planets: прогрессивные планеты
        - houses: прогрессивные дома
        - additional_points: прогрессивные точки (ASC, MC, Part of Fortune)
        - objects: все прогрессивные объекты
        - aspects: аспекты прогрессивных планет между собой
        - warnings: предупреждения
    """

    if settings is None:
        settings = dict(DEFAULT_SETTINGS)

        # Парсим дату и время рождения
    # Формат: "1990-05-15T14:30" или "1990-05-15T14:30:00"
    birth_datetime = datetime.fromisoformat(f"{birth['date']}T{birth['time']}")

    # Парсим только дату рождения (без времени) для вычисления возраста
    birth_date_only = datetime.fromisoformat(birth['date'])

    # Парсим дату прогрессии (без времени)
    progression_dt = datetime.fromisoformat(progression_date)

    # Вычисляем возраст в днях (используем только даты, без времени)
    # Это предотвращает отрицательный возраст, когда дата прогрессии
    # совпадает с датой рождения
    age_days_total = (progression_dt - birth_date_only).days

    # Возраст в годах (для информации и для расчёта прогрессивной даты)
    age_years = age_days_total / 365.25

    # Прогрессивная дата: дата рождения + возраст в годах (как количество дней)
    # Это и есть принцип вторичных прогрессий: 1 день после рождения = 1 год жизни
    # Например, для возраста 30 лет прогрессивная дата = дата рождения + 30 дней
    progressed_datetime = birth_datetime + timedelta(days=age_years)

    # Извлекаем дату и время для прогрессивной карты
    progressed_date_str = progressed_datetime.strftime("%Y-%m-%d")
    progressed_time_str = progressed_datetime.strftime("%H:%M")

    # Создаём данные для расчёта прогрессивной карты
    # Используем те же координаты и часовой пояс, что и для натальной карты
    progressed_birth = {
        "name": birth.get("name", "Progressed"),
        "date": progressed_date_str,
        "time": progressed_time_str,
        "latitude": birth["latitude"],
        "longitude": birth["longitude"],
        "utc_offset_hours": birth["utc_offset_hours"],
    }

    # Строим прогрессивную карту
    progressed_chart = build_natal_chart(progressed_birth, settings)

    # Формируем результат
    result = {
        "birth": birth,
        "progression_date": progression_date,
        "progression_type": "secondary",
        "age_days": age_days_total,
        "age_years": round(age_years, 2),
        "progressed_birth": progressed_birth,
        "planets": progressed_chart["planets"],
        "houses": progressed_chart["houses"],
        "additional_points": progressed_chart["additional_points"],
        "objects": progressed_chart["objects"],
        "aspects": progressed_chart.get("aspects", []),
        "warnings": progressed_chart.get("warnings", []),
    }

    return result


def calculate_solar_arc_progressions(birth, progression_date, settings=None):
    """
    Рассчитывает прогрессии солнечной дуги.

    Принцип: все натальные планеты продвигаются на то же расстояние,
    что и прогрессивное Солнце.

    Параметры:
        birth: данные рождения (словарь с полями:
               name, date, time, latitude, longitude, utc_offset_hours)
        progression_date: дата прогрессии (строка "ГГГГ-ММ-ДД")
        settings: настройки расчёта

    Возвращает:
        словарь с прогрессивной картой солнечной дуги:
        - birth: данные рождения
        - progression_date: дата прогрессии
        - age_years: возраст в годах
        - solar_arc: величина солнечной дуги
        - planets: прогрессивные планеты солнечной дуги
        - houses: прогрессивные дома солнечной дуги
        - additional_points: прогрессивные точки солнечной дуги
        - objects: все прогрессивные объекты солнечной дуги
        - warnings: предупреждения
    """

    if settings is None:
        settings = dict(DEFAULT_SETTINGS)

    # Сначала рассчитываем вторичные прогрессии, чтобы получить прогрессивное Солнце
    secondary = calculate_secondary_progressions(birth, progression_date, settings)

    # Находим натальное Солнце
    natal_chart = build_natal_chart(birth, settings)
    natal_sun = None
    for obj in natal_chart["planets"]:
        if obj["name"] == "Sun":
            natal_sun = obj
            break

    if natal_sun is None:
        return {
            "birth": birth,
            "progression_date": progression_date,
            "progression_type": "solar_arc",
            "warnings": ["Натальное Солнце не найдено. Прогрессии солнечной дуги не рассчитаны."],
        }

    # Находим прогрессивное Солнце
    progressed_sun = None
    for obj in secondary["planets"]:
        if obj["name"] == "Sun":
            progressed_sun = obj
            break

    if progressed_sun is None:
        return {
            "birth": birth,
            "progression_date": progression_date,
            "progression_type": "solar_arc",
            "warnings": ["Прогрессивное Солнце не найдено. Прогрессии солнечной дуги не рассчитаны."],
        }

    # Вычисляем солнечную дугу
    natal_sun_lon = natal_sun["longitude"]
    progressed_sun_lon = progressed_sun["longitude"]
    solar_arc = normalize_longitude(progressed_sun_lon - natal_sun_lon)

    # Продвигаем все натальные планеты на солнечную дугу
    solar_arc_planets = []
    for obj in natal_chart["planets"]:
        new_lon = normalize_longitude(obj["longitude"] + solar_arc)
        sign, degree_in_sign = sign_from_longitude(new_lon)

        new_obj = {
            "name": obj["name"],
            "type": obj.get("type", "planet"),
            "longitude": round(new_lon, 6),
            "sign": sign,
            "degree_in_sign": round(degree_in_sign, 6),
            "speed_longitude": 0.0,
            "retrograde": False,
        }
        solar_arc_planets.append(new_obj)

    # Продвигаем дополнительные точки (ASC, MC, Part of Fortune)
    solar_arc_additional = []
    for obj in natal_chart.get("additional_points", []):
        new_lon = normalize_longitude(obj["longitude"] + solar_arc)
        sign, degree_in_sign = sign_from_longitude(new_lon)

        new_obj = {
            "name": obj["name"],
            "type": obj.get("type", "point"),
            "longitude": round(new_lon, 6),
            "sign": sign,
            "degree_in_sign": round(degree_in_sign, 6),
        }
        solar_arc_additional.append(new_obj)

    # Объединяем все объекты
    all_objects = list(solar_arc_planets) + list(solar_arc_additional)

    # Вычисляем аспекты между прогрессивными объектами солнечной дуги
    aspects = calculate_aspects(all_objects, settings) if settings.get("enabled_aspects") else []

    # Формируем результат
    result = {
        "birth": birth,
        "progression_date": progression_date,
        "progression_type": "solar_arc",
        "age_days": secondary["age_days"],
        "age_years": secondary["age_years"],
        "solar_arc": round(solar_arc, 6),
        "planets": solar_arc_planets,
        "additional_points": solar_arc_additional,
        "objects": all_objects,
        "aspects": aspects,
        "warnings": secondary.get("warnings", []),
    }

    return result


def find_progression_aspects(natal_objects, progressed_objects, settings=None):
    """
    Находит аспекты между прогрессивными и натальными точками.

    Это основной способ использования прогрессий:
    аспекты прогрессивных планет к натальным точкам указывают
    на внутренние изменения и события.

    Параметры:
        natal_objects: список объектов натальной карты
        progressed_objects: список объектов прогрессивной карты
        settings: настройки аспектов и орбов

    Возвращает:
        список аспектов между прогрессивными и натальными точками
    """

    if settings is None:
        settings = DEFAULT_SETTINGS

    # Используем ту же логику, что и для транзитов:
    # прогрессивные объекты как "транзитные", натальные как "натальные"
    from .transits import find_transits_on_date

    aspects = find_transits_on_date(natal_objects, progressed_objects, settings)

    # Переименовываем поля для прогрессий
    progression_aspects = []
    for aspect in aspects:
        progression_aspect = {
            "progressed_planet": aspect["transit_planet"],
            "natal_point": aspect["natal_point"],
            "aspect": aspect["aspect"],
            "angle": aspect["angle"],
            "orb": aspect["orb"],
            "max_orb": aspect["max_orb"],
            "strength": aspect["strength"],
            "progressed_longitude": aspect["transit_longitude"],
            "natal_longitude": aspect["natal_longitude"],
        }
        progression_aspects.append(progression_aspect)

    return progression_aspects