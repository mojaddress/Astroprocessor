"""Суточные циклы: восход/заход Солнца, планетарные часы, лунные сутки, фазы.

Восход и заход вычисляются геометрически (высота Солнца над горизонтом)
через проверенные swe.calc_ut и swe.sidtime, БЕЗ swe.rise_trans: сигнатуры
и константы rise_trans различаются между версиями pyswisseph, а продукт
не должен зависеть от недокументированного API. Точность метода - лучше
минуты; полярный день и полярная ночь обрабатываются явно.

Халдейский порядок планет (убывание скорости): Сатурн, Юпитер, Марс,
Солнце, Венера, Меркурий, Луна. Первый час дня принадлежит управителю
дня недели, далее порядок циклически продолжается и в ночные часы.
"""
from __future__ import annotations

import math
from datetime import timedelta

from .ephemeris import ensure_swisseph, get_planet_position
from .time_service import datetime_to_jd, jd_to_datetime

# Стандартная высота центра Солнца на момент восхода/захода:
# учтены атмосферная рефракция и угловой радиус диска.
SUNRISE_ALTITUDE = -0.833

# Наклонение эклиптики (J2000). Погрешность медленного изменения наклона
# даёт ошибку восхода меньше минуты на горизонте десятилетий.
OBLIQUITY = 23.4392911

CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Управитель первого часа по дню недели (Monday=0 .. Sunday=6)
DAY_RULERS = {
    0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter",
    4: "Venus", 5: "Saturn", 6: "Sun",
}

PHASE_NAMES = [
    "Новолуние", "Растущий серп", "Первая четверть", "Растущая Луна",
    "Полнолуние", "Убывающая Луна", "Последняя четверть", "Убывающий серп",
]


def _jd_from_local(local_dt, utc_offset):
    return datetime_to_jd(local_dt - timedelta(hours=float(utc_offset)))


def _local_from_jd(jd, utc_offset):
    return jd_to_datetime(jd) + timedelta(hours=float(utc_offset))


def _sun_equatorial(jd_ut):
    """Экваториальные координаты Солнца (RA, Dec) в градусах."""
    lon, _ = get_planet_position(jd_ut, "Sun")
    lam = math.radians(lon)
    eps = math.radians(OBLIQUITY)
    ra = math.degrees(math.atan2(math.sin(lam) * math.cos(eps), math.cos(lam))) % 360.0
    dec = math.degrees(math.asin(math.sin(lam) * math.sin(eps)))
    return ra, dec


def local_sidereal_deg(jd_ut, longitude):
    """Локальное звёздное время в градусах."""
    import swisseph as swe
    return (swe.sidtime(jd_ut) * 15.0 + longitude) % 360.0


def sun_altitude(jd_ut, latitude, longitude):
    """Высота центра Солнца над горизонтом в градусах."""
    ra, dec = _sun_equatorial(jd_ut)
    lst = local_sidereal_deg(jd_ut, longitude)
    hour = math.radians(lst - ra)
    phi = math.radians(latitude)
    delta = math.radians(dec)
    sin_alt = (math.sin(phi) * math.sin(delta)
               + math.cos(phi) * math.cos(delta) * math.cos(hour))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))


def _refine_altitude(jd_low, jd_high, latitude, longitude):
    """Бисекция момента, когда высота Солнца равна SUNRISE_ALTITUDE."""
    def value(jd):
        return sun_altitude(jd, latitude, longitude) - SUNRISE_ALTITUDE

    low, high = jd_low, jd_high
    f_low = value(low)
    for _ in range(48):
        mid = (low + high) / 2.0
        f_mid = value(mid)
        if abs(f_mid) < 1e-7 or (high - low) < 1e-7:
            return mid
        if (f_low > 0.0) == (f_mid > 0.0):
            low, f_low = mid, f_mid
        else:
            high = mid
    return (low + high) / 2.0


def sun_events(day_local_midnight, latitude, longitude, utc_offset):
    """Восход и заход Солнца для локальных суток.

    Возвращает словарь: rise/set - Julian Day (UTC) или None, polar - флаг,
    polar_day - True при полярном дне (иначе полярная ночь).
    """
    ensure_swisseph()
    start = _jd_from_local(day_local_midnight, utc_offset)
    steps = 288  # шаг 5 минут
    rises, sets = [], []
    prev_alt = None
    prev_jd = None
    for index in range(steps + 1):
        jd = start + index / float(steps)
        alt = sun_altitude(jd, latitude, longitude)
        if prev_alt is not None:
            if prev_alt < SUNRISE_ALTITUDE <= alt:
                rises.append(_refine_altitude(prev_jd, jd, latitude, longitude))
            elif prev_alt >= SUNRISE_ALTITUDE > alt:
                sets.append(_refine_altitude(prev_jd, jd, latitude, longitude))
        prev_alt, prev_jd = alt, jd
    rise = rises[0] if rises else None
    sunset = sets[0] if sets else None
    polar = rise is None or sunset is None
    return {
        "rise": rise,
        "set": sunset,
        "polar": polar,
        "polar_day": bool(polar and sun_altitude(start + 0.5, latitude, longitude) > 0.0),
    }


def _chaldean_from(start_ruler):
    """24 управителя подряд, начиная с управителя дня."""
    offset = CHALDEAN_ORDER.index(start_ruler)
    return [CHALDEAN_ORDER[(offset + i) % 7] for i in range(24)]


def planetary_hours(day_local_midnight, latitude, longitude, utc_offset):
    """24 планетарных часа локальных суток (12 дневных + 12 ночных).

    Возвращает список словарей либо пустой список при полярном дне/ночи.
    """
    today = sun_events(day_local_midnight, latitude, longitude, utc_offset)
    if today["polar"]:
        return []
    tomorrow = sun_events(day_local_midnight + timedelta(days=1),
                          latitude, longitude, utc_offset)
    if tomorrow["rise"] is None:
        return []

    rise, sunset = today["rise"], today["set"]
    next_rise = tomorrow["rise"]
    day_step = (sunset - rise) / 12.0
    night_step = (next_rise - sunset) / 12.0
    rulers = _chaldean_from(DAY_RULERS[day_local_midnight.weekday()])

    hours = []
    cursor = rise
    for index in range(24):
        step = day_step if index < 12 else night_step
        start_jd, end_jd = cursor, cursor + step
        hours.append({
            "index": index + 1,
            "kind": "day" if index < 12 else "night",
            "ruler": rulers[index],
            "start_jd": start_jd,
            "end_jd": end_jd,
            "start_local": _local_from_jd(start_jd, utc_offset),
            "end_local": _local_from_jd(end_jd, utc_offset),
        })
        cursor = end_jd
    return hours


def moon_sun_elongation(jd_ut):
    """Угловое расстояние Луны от Солнца, 0..360."""
    sun, _ = get_planet_position(jd_ut, "Sun")
    moon, _ = get_planet_position(jd_ut, "Moon")
    return (moon - sun) % 360.0


def _lunar_day_from_elongation(elongation):
    """Лунные сутки 1..30: каждые 12 градусов элонгации."""
    return int(float(elongation) // 12.0) + 1


def _phase_from_elongation(elongation):
    index = int((float(elongation) + 22.5) % 360.0 // 45.0)
    return PHASE_NAMES[index]


def lunar_day(jd_ut):
    return _lunar_day_from_elongation(moon_sun_elongation(jd_ut))


def moon_phase(jd_ut):
    return _phase_from_elongation(moon_sun_elongation(jd_ut))
