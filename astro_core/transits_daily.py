"""
Транзиты: текущее небо против натальной карты (итерация 22).

Модуль не зависит от эфемерид: карта неба строится снаружи
(build_natal_chart на нужную дату) и передаётся сюда или через get_sky.
Кросс-фильтр "транзит-натал" — суффикс имён неба "_t".
"""

from datetime import date, timedelta
from typing import Callable, Dict, List, Optional

from .aspects import calculate_aspects
from .constants import get_planet_name_ru
from .interpretations import ASPECT_INFO
from .controllers.synastry_controller import SynastryController

SKY_SUFFIX = "_t"

DEFAULT_ORBS = {
    "conjunction": 8.0,
    "opposition": 8.0,
    "square": 6.0,
    "trine": 6.0,
    "sextile": 4.0,
}


def make_sky_birth_from_chart(natal_chart: Dict, d: date, time: str = "12:00") -> Dict:
    """Данные рождения для карты неба на дату d (география из натала)."""
    birth = dict(natal_chart.get("birth", {}))
    birth["name"] = "небо"
    birth["date"] = d.strftime("%Y-%m-%d")
    birth["time"] = time
    return birth


def transit_aspects(natal_chart: Dict, sky_chart: Dict, orbs: Optional[Dict] = None) -> List[Dict]:
    """Аспекты транзитных планет к натальным точкам (только между картами)."""
    if orbs is None:
        orbs = dict(DEFAULT_ORBS)
    natal_objects = [dict(o) for o in natal_chart.get("planets", [])]
    sky_objects = []
    for obj in sky_chart.get("planets", []):
        tagged = dict(obj)
        tagged["name"] = f"{obj['name']}{SKY_SUFFIX}"
        sky_objects.append(tagged)

    settings = {"enabled_aspects": list(orbs.keys()), "orbs": orbs}
    all_aspects = calculate_aspects(natal_objects + sky_objects, settings)

    result = []
    for aspect in all_aspects:
        pa = aspect["point_a"]
        pb = aspect["point_b"]
        a_sky = pa.endswith(SKY_SUFFIX)
        b_sky = pb.endswith(SKY_SUFFIX)
        if a_sky == b_sky:
            continue
        if a_sky:
            transit_name, natal_name = pa[: -len(SKY_SUFFIX)], pb
        else:
            transit_name, natal_name = pb[: -len(SKY_SUFFIX)], pa
        result.append({
            "transit_planet": transit_name,
            "natal_point": natal_name,
            "aspect": aspect["aspect"],
            "orb": aspect["orb"],
            "score": SynastryController.ASPECT_SCORES.get(aspect["aspect"], 0),
        })
    result.sort(key=lambda x: abs(x["orb"]))
    return result


def scan_periods(natal_chart, start, days, get_sky, orbs=None):
    """Периоды действия транзитных аспектов по days дней (шаг 1 день)."""
    if orbs is None:
        orbs = dict(DEFAULT_ORBS)
    active = {}
    periods = []

    for i in range(days):
        d = start + timedelta(days=i)
        aspects = transit_aspects(natal_chart, get_sky(d), orbs)
        seen = set()
        for a in aspects:
            k = (a["transit_planet"], a["natal_point"], a["aspect"])
            seen.add(k)
            orb_abs = abs(a["orb"])
            if k not in active:
                active[k] = {"start": d, "end": d, "exact_date": d,
                             "min_orb": orb_abs, "score": a["score"]}
            else:
                rec = active[k]
                rec["end"] = d
                if orb_abs < rec["min_orb"]:
                    rec["min_orb"] = orb_abs
                    rec["exact_date"] = d
        for k in list(active.keys()):
            if k not in seen:
                periods.append(_period_dict(k, active.pop(k)))
    for k, rec in active.items():
        periods.append(_period_dict(k, rec))
    periods.sort(key=lambda p: p["start"])
    return periods


def _period_dict(key, rec):
    transit_name, natal_name, aspect = key
    return {
        "transit_planet": transit_name,
        "natal_point": natal_name,
        "aspect": aspect,
        "start": rec["start"],
        "end": rec["end"],
        "exact_date": rec["exact_date"],
        "score": rec["score"],
    }


def summarize_transits(natal_chart, aspects, d, periods=None):
    """Текстовая сводка: поддержка/напряжение сегодня + периоды."""
    name = natal_chart.get("birth", {}).get("name", "карта")
    lines = [f"Транзиты на {d.strftime('%Y-%m-%d')} — {name}", ""]
    lines.append("Поддержка сегодня:")
    supportive = [a for a in aspects if a["score"] > 0]
    if supportive:
        for a in supportive:
            info = ASPECT_INFO.get(a["aspect"], {})
            lines.append(
                f"  Транзит {get_planet_name_ru(a['transit_planet'])} "
                f"{info.get('name', a['aspect'])} "
                f"натал {get_planet_name_ru(a['natal_point'])} "
                f"(орб {abs(a['orb']):.1f}) — гармоничный аспект, поддержка")
    else:
        lines.append("  — нет")
    lines.append("")
    lines.append("Напряжение сегодня:")
    tension = [a for a in aspects if a["score"] < 0]
    if tension:
        for a in tension:
            info = ASPECT_INFO.get(a["aspect"], {})
            lines.append(
                f"  Транзит {get_planet_name_ru(a['transit_planet'])} "
                f"{info.get('name', a['aspect'])} "
                f"натал {get_planet_name_ru(a['natal_point'])} "
                f"(орб {abs(a['orb']):.1f}) — напряжённый аспект, осторожность")
    else:
        lines.append("  — нет")
    if periods:
        lines.append("")
        lines.append("Периоды действия:")
        for p in periods:
            info = ASPECT_INFO.get(p["aspect"], {})
            tone = "гармоничный" if p["score"] > 0 else "напряжённый"
            lines.append(
                f"  Транзит {get_planet_name_ru(p['transit_planet'])} "
                f"{info.get('name', p['aspect'])} "
                f"натал {get_planet_name_ru(p['natal_point'])}: "
                f"{p['start'].strftime('%Y-%m-%d')} – {p['end'].strftime('%Y-%m-%d')} "
                f"(точно {p['exact_date'].strftime('%Y-%m-%d')}) — {tone}")
    return "\n".join(lines)
