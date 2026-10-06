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
        progression_date: дата прогрессии (строка "ГГГГ-ММ-ДД" или datetime.date)
        settings: настройки расчёта

    Возвращает:
        словарь с прогрессивной картой
    """

    if settings is None:
        settings = dict(DEFAULT_SETTINGS)

    # Парсим дату и время рождения
    birth_datetime = datetime.fromisoformat(f"{birth['date']}T{birth['time']}")

    # Парсим только дату рождения (без времени) для вычисления возраста
    birth_date_only = datetime.fromisoformat(birth['date'])

    # Парсим дату прогрессии (поддержка строки и date объекта)
    if isinstance(progression_date, str):
        progression_dt = datetime.fromisoformat(progression_date)
    else:
        # Assume it's a date/datetime object
        progression_dt = datetime.combine(progression_date, datetime.min.time())

    # Вычисляем возраст в днях (используем только даты, без времени)
    age_days_total = (progression_dt - birth_date_only).days

    # Защита: дата прогрессии не может быть раньше даты рождения
    if age_days_total < 0:
        return {
            "birth": birth,
            "progression_date": progression_date,
            "progression_type": "secondary",
            "age_days": age_days_total,
            "age_years": 0,
            "planets": [],
            "houses": [],
            "additional_points": [],
            "objects": [],
            "aspects": [],
            "warnings": [
                f"Дата прогрессии ({progression_date}) раньше даты рождения "
                f"({birth['date']}). Прогрессии не рассчитаны."
            ],
        }

    # Возраст в годах
    age_years = age_days_total / 365.25

    # Принцип вторичных прогрессий:
    # 1 день после рождения = 1 год жизни.
    # Если возраст 30 лет, прибавляем 30 дней к моменту рождения.
    progressed_datetime = birth_datetime + timedelta(days=age_years)

    progressed_date_str = progressed_datetime.strftime("%Y-%m-%d")
    progressed_time_str = progressed_datetime.strftime("%H:%M")

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
        birth: данные рождения
        progression_date: дата прогрессии (строка "ГГГГ-ММ-ДД")
        settings: настройки расчёта

    Возвращает:
        словарь с прогрессивной картой солнечной дуги
    """

    if settings is None:
        settings = dict(DEFAULT_SETTINGS)

    # Сначала рассчитываем вторичные прогрессии, чтобы получить прогрессивное Солнце
    secondary = calculate_secondary_progressions(birth, progression_date, settings)

    # Если вторичные прогрессии не получились (например, дата раньше рождения)
    if not secondary.get("planets"):
        return {
            "birth": birth,
            "progression_date": progression_date,
            "progression_type": "solar_arc",
            "age_days": secondary.get("age_days", 0),
            "age_years": secondary.get("age_years", 0),
            "solar_arc": 0.0,
            "planets": [],
            "additional_points": [],
            "objects": [],
            "aspects": [],
            "warnings": secondary.get("warnings", []),
        }

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
            "warnings": [
                "Натальное Солнце не найдено. "
                "Прогрессии солнечной дуги не рассчитаны."
            ],
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
            "warnings": [
                "Прогрессивное Солнце не найдено. "
                "Прогрессии солнечной дуги не рассчитаны."
            ],
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

    all_objects = list(solar_arc_planets) + list(solar_arc_additional)

    # Аспекты между прогрессивными объектами солнечной дуги
    aspects = []
    if settings.get("enabled_aspects"):
        aspects = calculate_aspects(all_objects, settings)

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

    Параметры:
        natal_objects: список объектов натальной карты
        progressed_objects: список объектов прогрессивной карты
        settings: настройки аспектов и орбов

    Возвращает:
        список аспектов между прогрессивными и натальными точками
    """

    if settings is None:
        settings = DEFAULT_SETTINGS

    from .transits import find_transits_on_date

    aspects = find_transits_on_date(natal_objects, progressed_objects, settings)

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