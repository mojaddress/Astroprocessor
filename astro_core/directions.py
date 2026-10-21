"""
Дирекции солнечной дуги (итерация 27, финал).

Принцип: 1 год жизни = 1 день после рождения = ~1° дуги.
Прогрессивное Солнце = Солнце на дату (день рождения + возраст в годах).
Дуга = долгота прогрессивного Солнца - долгота натального Солнца.
Дирекционная планета = натальная + дуга.
"""
from datetime import date as _date, datetime, timedelta
from typing import Dict, List, Optional

from .aspects import calculate_aspects
from .constants import DEFAULT_SETTINGS
from .ephemeris import calculate_objects, initialize_ephemeris
from .controllers.synastry_controller import SynastryController
from .time_service import datetime_to_jd
from .utils import sign_from_longitude

DIR_SUFFIX = "_d"

DEFAULT_ORBS = {
    "conjunction": 8.0, "opposition": 8.0, "square": 6.0,
    "trine": 6.0, "sextile": 4.0,
}


def _sun_longitude(chart: Dict) -> float:
    for p in chart.get("planets", []):
        if p.get("name") == "Sun":
            return p.get("longitude", 0.0)
    return 0.0


def _years_between(natal_date: _date, target_date: _date) -> int:
    """Полных лет жизни (округление вниз)."""
    return target_date.year - natal_date.year - (
        1 if (target_date.month, target_date.day) < (natal_date.month, natal_date.day) else 0
    )


def _progressive_sun_longitude(natal_date: _date, target_date: _date) -> float:
    """Долгота прогрессивного Солнца: небо на день рождения + возраст в годах (дней)."""
    age_years = _years_between(natal_date, target_date)
    prog_date = natal_date + timedelta(days=age_years)
    prog_jd = datetime_to_jd(datetime(prog_date.year, prog_date.month, prog_date.day, 12, 0))
    initialize_ephemeris(dict(DEFAULT_SETTINGS))
    objs, _ = calculate_objects(prog_jd, dict(DEFAULT_SETTINGS))
    sun = next((o for o in objs if o.get("name") == "Sun"), None)
    return sun["longitude"] if sun else 0.0


def solar_arc(natal_chart: Dict, target_date: _date) -> float:
    """Дуга солнечной дуги (в градусах) на целевую дату."""
    natal_date = _date.fromisoformat(natal_chart["birth"]["date"])
    prog_lon = _progressive_sun_longitude(natal_date, target_date)
    natal_lon = _sun_longitude(natal_chart)
    return (prog_lon - natal_lon) % 360.0


def directed_planets(natal_chart: Dict, arc: float) -> List[Dict]:
    """Дирекционные планеты: натальные, сдвинутые на дугу."""
    out = []
    for p in natal_chart.get("planets", []):
        lon = (p.get("longitude", 0.0) + arc) % 360.0
        sign, deg = sign_from_longitude(lon)
        out.append({
            "name": p.get("name"),
            "longitude": lon,
            "sign": sign,
            "degree_in_sign": deg,
            "house": None,
            "retrograde": False,
        })
    return out


def calculate_directions(natal_chart: Dict, target_date: _date,
                         orbs: Optional[Dict] = None) -> Dict:
    """Полный расчёт дирекций: дуга, планеты, аспекты к натальным точкам."""
    if orbs is None:
        orbs = dict(DEFAULT_ORBS)
    arc = solar_arc(natal_chart, target_date)
    planets = directed_planets(natal_chart, arc)

    natal_objects = [dict(o) for o in natal_chart.get("planets", [])]
    for pt in natal_chart.get("additional_points", []):
        natal_objects.append(dict(pt))
    dir_objects = []
    for p in planets:
        q = dict(p)
        q["name"] = f"{p['name']}{DIR_SUFFIX}"
        dir_objects.append(q)

    settings = {"enabled_aspects": list(orbs.keys()), "orbs": orbs}
    all_aspects = calculate_aspects(natal_objects + dir_objects, settings)

    aspects = []
    for a in all_aspects:
        pa, pb = a["point_a"], a["point_b"]
        a_dir = pa.endswith(DIR_SUFFIX)
        b_dir = pb.endswith(DIR_SUFFIX)
        if a_dir == b_dir:
            continue
        if a_dir:
            d_name, n_name = pa[:-len(DIR_SUFFIX)], pb
        else:
            d_name, n_name = pb[:-len(DIR_SUFFIX)], pa
        aspects.append({
            "dir_planet": d_name,
            "natal_point": n_name,
            "aspect": a["aspect"],
            "orb": a["orb"],
            "score": SynastryController.ASPECT_SCORES.get(a["aspect"], 0),
        })
    aspects.sort(key=lambda x: abs(x["orb"]))
    return {"arc": arc, "planets": planets, "aspects": aspects}
