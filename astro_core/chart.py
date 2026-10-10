import copy
from datetime import datetime, timezone

from .constants import DEFAULT_SETTINGS
from .time_service import parse_local_datetime, datetime_to_jd
from .ephemeris import (
    calculate_objects,
    calculate_houses,
    initialize_ephemeris,
    SWISSEPH_AVAILABLE,
)
from .points import is_day_chart, part_of_fortune
from .utils import normalize_longitude, sign_from_longitude, house_for_longitude
from .aspects import calculate_aspects

# Версия формата карты (обновляется при изменении структуры результата)
CHART_FORMAT_VERSION = "0.9.1"


def _validate_birth_data(birth):
    """
    Проверяет корректность данных рождения.

    Возвращает:
        список предупреждений (некритичные проблемы)

    Исключения:
        ValueError при критичных ошибках (неверные данные)
    """
    warnings = []

    # Проверка даты рождения
    try:
        birth_date = datetime.fromisoformat(birth["date"])
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Неверный формат даты рождения: {birth.get('date')}. "
            "Ожидается ГГГГ-ММ-ДД."
        ) from e

    current_date = datetime.now()
    if birth_date > current_date:
        warnings.append(
            f"Дата рождения ({birth['date']}) в будущем. "
            "Проверьте правильность ввода."
        )

    # Проверка времени рождения
    time_str = birth["time"]
    try:
        time_parts = str(time_str).split(":")
        if len(time_parts) < 2:
            raise ValueError("Время должно быть в формате ЧЧ:ММ")

        hours = int(time_parts[0])
        minutes = int(time_parts[1])

        if hours < 0 or hours > 23:
            raise ValueError(f"Часы должны быть от 0 до 23, получено {hours}")
        if minutes < 0 or minutes > 59:
            raise ValueError(f"Минуты должны быть от 0 до 59, получено {minutes}")
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Неверный формат времени рождения: {birth.get('time')}. {e}"
        ) from e

    # Проверка координат
    try:
        latitude = float(birth["latitude"])
        longitude = float(birth["longitude"])
    except (ValueError, TypeError) as e:
        raise ValueError(
            "Координаты должны быть числами: "
            f"latitude={birth.get('latitude')}, longitude={birth.get('longitude')}"
        ) from e

    if latitude < -90 or latitude > 90:
        raise ValueError(
            f"Широта должна быть от -90 до 90, получено {latitude}"
        )

    if longitude < -180 or longitude > 180:
        raise ValueError(
            f"Долгота должна быть от -180 до 180, получено {longitude}"
        )

    # Проверка UTC offset
    try:
        utc_offset = float(birth["utc_offset_hours"])
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"UTC offset должен быть числом, получено: {birth.get('utc_offset_hours')}"
        ) from e

    if utc_offset < -12 or utc_offset > 14:
        warnings.append(
            f"UTC offset ({utc_offset}) выходит за пределы [-12, +14]. "
            "Проверьте правильность часового пояса."
        )

    # Проверка имени (не критично, но предупреждаем)
    name = birth.get("name", "")
    if not str(name).strip():
        warnings.append("Имя карты пустое. Рекомендуется задать имя.")

    return warnings


def _filter_enabled_planets(objects, enabled_planets):
    """
    Отфильтровывает список объектов, оставляя только включённые планеты.

    Это реализация «исключения из расчётов» (Решение №3):
    исключённые планеты не попадают в результат карты, поэтому
    они автоматически не участвуют в аспектах, транзитах и прогрессиях.

    Объекты, не являющиеся планетами (лунные узлы, Хирон), не затрагиваются —
    они управляются собственными флагами include_nodes / include_chiron.

    Параметры:
        objects: список рассчитанных объектов
        enabled_planets: список имён планет, которые нужно оставить.
                         Если None — фильтрация не выполняется
                         (обратная совместимость со старым поведением).

    Возвращает:
        отфильтрованный список объектов
    """
    if enabled_planets is None:
        return objects

    enabled_set = set(enabled_planets)
    return [
        obj for obj in objects
        if obj.get("type") != "planet" or obj["name"] in enabled_set
    ]


def build_natal_chart(birth, settings=None):
    """
    Собирает полную натальную карту.

    Параметры:
        birth: данные рождения
        settings: настройки расчёта

    Настройки могут содержать:
        zodiac: тип зодиака - "tropical" или "sidereal" (по умолчанию "tropical")
        ayanamsha: система ayanamsha для сидерического зодиака (по умолчанию "lahiri")
        enabled_planets: список планет, которые должны остаться в карте.
                         Если отсутствует или None — рассчитываются все планеты.
                         Управляется профилями отображения через
                         display_profiles.apply_profile_to_settings().

    Возвращает:
        словарь с картой, готовый к сохранению в JSON
    """

    if not SWISSEPH_AVAILABLE:
        raise RuntimeError(
            "Swiss Ephemeris is not installed. "
            "Install with: py -3.11 -m pip install pyswisseph"
        )

    if settings is None:
        settings = copy.deepcopy(DEFAULT_SETTINGS)
    else:
        merged_settings = copy.deepcopy(DEFAULT_SETTINGS)

        for key, value in settings.items():
            if key == "orbs" and isinstance(value, dict):
                merged_settings["orbs"].update(value)
            else:
                merged_settings[key] = value

        settings = merged_settings

    required_fields = [
        "name",
        "date",
        "time",
        "latitude",
        "longitude",
        "utc_offset_hours",
    ]

    for field_name in required_fields:
        if field_name not in birth:
            raise ValueError(f"Birth data is missing required field: {field_name}")

    # Валидация входных данных
    warnings = _validate_birth_data(birth)

    initialize_ephemeris(settings)

    local_datetime, utc_datetime = parse_local_datetime(
        birth["date"],
        birth["time"],
        birth["utc_offset_hours"],
    )

    julian_day = datetime_to_jd(utc_datetime)

    # Передаём координаты для расчёта домов и углов
    settings["latitude"] = birth.get("latitude", 0.0)
    settings["longitude"] = birth.get("longitude", 0.0)

    objects, object_warnings = calculate_objects(julian_day, settings)
    warnings.extend(object_warnings)

    houses = []
    asc_longitude = None
    mc_longitude = None

    try:
        houses, asc_longitude, mc_longitude = calculate_houses(
            julian_day,
            birth["latitude"],
            birth["longitude"],
            settings,
        )
    except Exception as error:
        warnings.append(f"Houses were not calculated: {error}")

    cusp_longitudes = [house["longitude"] for house in houses]

    for obj in objects:
        obj["house"] = house_for_longitude(cusp_longitudes, obj["longitude"])

    # ============================================================
    # Фильтр «включённые планеты» из профиля отображения (шаг 2.2).
    # Применяется ДО расчёта Part of Fortune и аспектов, чтобы
    # исключённые планеты не участвовали ни в каких дальнейших расчётах.
    # ============================================================
    objects = _filter_enabled_planets(objects, settings.get("enabled_planets"))

    all_objects = list(objects)
    additional_points = []

    if settings.get("include_angles", True) and asc_longitude is not None and mc_longitude is not None:
        angle_points = [
            ("ASC", asc_longitude),
            ("MC", mc_longitude),
        ]
        if settings.get("include_dsc", True):
            angle_points.append(("DSC", (asc_longitude + 180.0) % 360.0))

        for name, longitude in angle_points:
            normalized = normalize_longitude(longitude)
            sign, degree_in_sign = sign_from_longitude(normalized)

            angle_object = {
                "name": name,
                "longitude": round(normalized, 6),
                "sign": sign,
                "degree_in_sign": round(degree_in_sign, 6),
                "house": house_for_longitude(cusp_longitudes, normalized),
                "type": "angle",
            }

            all_objects.append(angle_object)
            additional_points.append(angle_object)

    if settings.get("include_part_of_fortune", True):
        if asc_longitude is None:
            warnings.append("Part of Fortune skipped: ASC was not calculated.")
        else:
            sun = next((p for p in objects if p["name"] == "Sun"), None)
            moon = next((p for p in objects if p["name"] == "Moon"), None)

            if sun is None or moon is None:
                warnings.append("Part of Fortune skipped: Sun or Moon not found.")
            else:
                day_chart = is_day_chart(sun["longitude"], asc_longitude)
                pof_longitude = part_of_fortune(
                    asc_longitude,
                    sun["longitude"],
                    moon["longitude"],
                    day_chart,
                )

                sign, degree_in_sign = sign_from_longitude(pof_longitude)

                pof_object = {
                    "name": "PartOfFortune",
                    "longitude": round(pof_longitude, 6),
                    "sign": sign,
                    "degree_in_sign": round(degree_in_sign, 6),
                    "house": house_for_longitude(cusp_longitudes, pof_longitude),
                    "type": "point",
                    "day_chart": day_chart,
                }

                all_objects.append(pof_object)
                additional_points.append(pof_object)

    aspects = []

    if settings.get("enabled_aspects"):
        aspects = calculate_aspects(all_objects, settings)

    zodiac_type = settings.get("zodiac", "tropical")
    ayanamsha = settings.get("ayanamsha", "lahiri")

    return {
        "meta": {
            "project": "Astro Processor",
            "stage": CHART_FORMAT_VERSION,
            "mode": "modular",
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "zodiac": zodiac_type,
            "ayanamsha": ayanamsha if zodiac_type == "sidereal" else None,
        },
        "birth": birth,
        "settings": settings,
        "local_datetime": local_datetime.isoformat(),
        "utc_datetime": utc_datetime.isoformat(),
        "julian_day": round(julian_day, 8),
        "planets": objects,
        "additional_points": additional_points,
        "objects": all_objects,
        "houses": houses,
        "aspects": aspects,
        "warnings": warnings,
    }