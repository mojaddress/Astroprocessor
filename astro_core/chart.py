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


def build_natal_chart(birth, settings=None):
    """
    Собирает полную натальную карту.

    Параметры:
        birth: данные рождения
        settings: настройки расчёта

    Настройки могут содержать:
        zodiac: тип зодиака - "tropical" или "sidereal" (по умолчанию "tropical")
        ayanamsha: система ayanamsha для сидерического зодиака (по умолчанию "lahiri")

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

    warnings = []

    # Сидерический зодиак поддерживается (добавлен в Этапе 08)
    # Никаких дополнительных предупреждений не нужно

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

    all_objects = list(objects)
    additional_points = []

    if settings.get("include_angles", True) and asc_longitude is not None and mc_longitude is not None:
        angle_points = [
            ("ASC", asc_longitude),
            ("MC", mc_longitude),
        ]

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

    # Определяем информацию о зодиаке для мета-данных
    zodiac_type = settings.get("zodiac", "tropical")
    ayanamsha = settings.get("ayanamsha", "lahiri")

    return {
        "meta": {
            "project": "Astro Processor",
            "stage": "0.8.0",
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