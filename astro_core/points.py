from .utils import normalize_longitude


def is_day_chart(sun_longitude, asc_longitude):
    """
    Упрощённое определение дневной карты.

    Используется для расчёта Part of Fortune.

    Логика:
        Если Солнце находится в верхней полусфере относительно ASC,
        считаем карту дневной.
    """

    diff = normalize_longitude(sun_longitude - asc_longitude)
    return diff < 180.0


def part_of_fortune(asc_longitude, sun_longitude, moon_longitude, day_chart):
    """
    Рассчитывает Part of Fortune.

    Формула:
        Day:   ASC + Moon - Sun
        Night: ASC + Sun - Moon
    """

    if day_chart:
        result = asc_longitude + moon_longitude - sun_longitude
    else:
        result = asc_longitude + sun_longitude - moon_longitude

    return normalize_longitude(result)

def cross_of_fate(sun_longitude: float, moon_longitude: float) -> float:
    """Крест судьбы: середина дуги Солнце–Луна (итерация 34, D-65)."""
    diff = (moon_longitude - sun_longitude + 180.0) % 360.0 - 180.0
    return (sun_longitude + diff / 2.0) % 360.0
