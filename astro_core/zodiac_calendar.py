"""
Календарь знаков зодиака: периоды знаков для года (тропический зодиак).

Точность: ±1 день (солнечные ингрессии на 12:00 UTC каждого дня).
"""

from datetime import date, datetime, timedelta

from .constants import DEFAULT_SETTINGS, get_sign_name_ru
from .ephemeris import calculate_objects, initialize_ephemeris
from .time_service import datetime_to_jd
from .utils import sign_from_longitude


def sign_periods(year: int):
    """Возвращает список сегментов (sign, start_date, end_date) за год."""
    initialize_ephemeris(dict(DEFAULT_SETTINGS))
    segments = []
    cur_sign = None
    start = None
    d = date(year, 1, 1)
    end = date(year, 12, 31)
    while d <= end:
        jd = datetime_to_jd(datetime(d.year, d.month, d.day, 12, 0))
        objs, _ = calculate_objects(jd, dict(DEFAULT_SETTINGS))
        sun = next((o for o in objs if o.get("name") == "Sun"), None)
        if sun is None:
            break
        sign = sign_from_longitude(sun["longitude"])[0]
        if sign != cur_sign:
            if cur_sign is not None:
                segments.append((cur_sign, start, d - timedelta(days=1)))
            cur_sign, start = sign, d
        d += timedelta(days=1)
    if cur_sign is not None:
        segments.append((cur_sign, start, end))
    return segments


def format_sign_periods(segments) -> str:
    lines = []
    for sign, s, e in segments:
        lines.append(f"{get_sign_name_ru(sign)}: {s.strftime('%d.%m')} – {e.strftime('%d.%m')}")
    return "\n".join(lines)
