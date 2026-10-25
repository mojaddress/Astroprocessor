"""
Солнечные обращения (соляры) — итерация 30.
Момент обращения: транзитное Солнце достигает натальной долготы Солнца.
Поиск: почасовое сканирование +/-2 суток от дня рождения + бисекция до минут.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional

from .chart import build_natal_chart
from .constants import DEFAULT_SETTINGS, get_planet_name_ru, get_sign_name_ru
from .ephemeris import calculate_objects, initialize_ephemeris
from .time_service import datetime_to_jd


def _sun_lon(jd: float) -> float:
    objs, _ = calculate_objects(jd, dict(DEFAULT_SETTINGS))
    for o in objs:
        if o.get("name") == "Sun":
            return o["longitude"]
    return 0.0


def _signed_diff(a: float, b: float) -> float:
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


def solar_return_moment(natal_chart: Dict, year: int) -> datetime:
    """Момент (UTC), когда транзитное Солнце равно натальному в заданном году."""
    initialize_ephemeris(dict(DEFAULT_SETTINGS))
    natal_sun = next(p["longitude"] for p in natal_chart["planets"]
                     if p["name"] == "Sun")
    birth = natal_chart["birth"]
    bd = datetime.fromisoformat(f"{birth['date']}T{birth['time']}")
    start = datetime(year, bd.month, bd.day, 0, 0) - timedelta(days=2)
    prev_t = start
    prev_d = _signed_diff(_sun_lon(datetime_to_jd(prev_t)), natal_sun)
    bracket = None
    t = start
    for _ in range(5 * 24):
        t = t + timedelta(hours=1)
        d = _signed_diff(_sun_lon(datetime_to_jd(t)), natal_sun)
        if prev_d < 0 <= d:
            bracket = (prev_t, t)
            break
        prev_t, prev_d = t, d
    if bracket is None:
        return min((start + timedelta(hours=h) for h in range(5 * 24)),
                   key=lambda tt: abs(_signed_diff(
                       _sun_lon(datetime_to_jd(tt)), natal_sun)))
    lo, hi = bracket
    for _ in range(40):
        mid = lo + (hi - lo) / 2
        if _signed_diff(_sun_lon(datetime_to_jd(mid)), natal_sun) < 0:
            lo = mid
        else:
            hi = mid
    return lo + (hi - lo) / 2


def calculate_solar_return(natal_chart: Dict, year: int,
                           latitude: float, longitude: float,
                           settings: Optional[Dict] = None) -> Dict:
    """Карта соляра на момент обращения для указанных координат."""
    moment = solar_return_moment(natal_chart, year)
    name = natal_chart.get("birth", {}).get("name", "Карта")
    birth = {
        "name": f"{name} — соляр {year}",
        "date": moment.date().isoformat(),
        "time": moment.strftime("%H:%M:%S"),
        "latitude": latitude,
        "longitude": longitude,
        "utc_offset_hours": 0.0,
    }
    merged = dict(DEFAULT_SETTINGS)
    if settings:
        merged.update(settings)
    chart = build_natal_chart(birth, merged)
    return {"moment_utc": moment, "chart": chart}


def summarize_solar_return(sr_chart: Dict, year: int, moment: datetime) -> str:
    planets = {p["name"]: p for p in sr_chart["planets"]}
    points = {p["name"]: p for p in sr_chart.get("additional_points", [])}
    lines = [f"Солнечное обращение {year}",
             f"Момент (UTC): {moment.strftime('%Y-%m-%d %H:%M')}"]
    sun = planets.get("Sun")
    if sun:
        lines.append(f"Солнце года: {get_sign_name_ru(sun['sign'])}, "
                     f"дом {sun.get('house') or '—'} — главная сфера года.")
    asc = points.get("ASC")
    if asc:
        lines.append(f"ASC возврата: {get_sign_name_ru(asc['sign'])} — "
                     f"«фасад» года, стиль поведения.")
    moon = planets.get("Moon")
    if moon:
        lines.append(f"Луна возврата: {get_sign_name_ru(moon['sign'])} — "
                     f"эмоциональный фон года.")
    lines.append("")
    lines.append("Ключевые аспекты возврата:")
    for a in sr_chart.get("aspects", [])[:5]:
        lines.append(f"- {get_planet_name_ru(a['point_a'])} — "
                     f"{get_planet_name_ru(a['point_b'])}: {a['aspect']} "
                     f"(орб {a['orb']:.2f})")
    return "\n".join(lines)
