"""Средние точки и планетарные картины (VXMP).

Средняя точка пары A/B - середина кратчайшей дуги между ними.
Дальняя средняя точка отличается на 180 градусов.
90-градусный дайал (шкала Эбертина) - свёртка долготы по модулю 90.

Практическая ценность - занятые средние точки: третья планета стоит
на средней точке пары в пределах орба. Это и есть планетарная картина.

Запуск из командной строки:
  py -3.11 -m astro_core.midpoints
  py -3.11 -m astro_core.midpoints --orb 1.0 --all
"""
from __future__ import annotations

import argparse
import sys
from itertools import combinations

from .constants import get_planet_name_ru, get_sign_name_ru
from .utils import normalize_longitude, sign_from_longitude

DEFAULT_MIDPOINT_ORB = 1.5


def _longitudes(objects):
    result = {}
    for obj in objects or []:
        name = obj.get("name")
        lon = obj.get("longitude")
        if name and lon is not None:
            result[name] = float(lon)
    return result


def angular_distance(a, b):
    """Кратчайшее угловое расстояние 0..180."""
    diff = abs(float(a) - float(b)) % 360.0
    return 360.0 - diff if diff > 180.0 else diff


def midpoint_longitude(lon_a, lon_b):
    """Ближняя средняя точка пары (середина кратчайшей дуги).

    MIDPOINT_SYM_V1: для антиподальных точек (разница ровно 180) обе
    дуги равны, поэтому отсчёт ведётся от меньшей долготы - функция
    симметрична и детерминирована.
    """
    a = float(lon_a) % 360.0
    b = float(lon_b) % 360.0
    delta = (b - a) % 360.0
    if delta > 180.0 or (delta == 180.0 and a > b):
        delta -= 360.0
    return normalize_longitude(a + delta / 2.0)


def dial90(lon):
    """Свёртка в 90-градусный дайал."""
    return float(lon) % 90.0


def all_midpoints(objects):
    """Все пары объектов: ближняя и дальняя средние точки."""
    points = _longitudes(objects)
    result = []
    for name_a, name_b in combinations(sorted(points), 2):
        near = midpoint_longitude(points[name_a], points[name_b])
        far = normalize_longitude(near + 180.0)
        sign, degree = sign_from_longitude(near)
        result.append({
            "pair": f"{name_a}/{name_b}",
            "a": name_a,
            "b": name_b,
            "midpoint": round(near, 6),
            "opposite": round(far, 6),
            "sign": sign,
            "degree_in_sign": round(degree, 6),
            "dial90": round(dial90(near), 6),
        })
    result.sort(key=lambda item: item["dial90"])
    return result


def occupied_midpoints(objects, orb=DEFAULT_MIDPOINT_ORB, include_opposite=True):
    """Занятые средние точки: третья планета на средней точке пары.

    Планета не может занимать собственную среднюю точку - исключается.
    Результат отсортирован по орбу: самые точные картины первыми.
    """
    points = _longitudes(objects)
    limit = float(orb)
    if limit <= 0.0:
        return []
    result = []
    for entry in all_midpoints(objects):
        targets = [("midpoint", entry["midpoint"])]
        if include_opposite:
            targets.append(("opposite", entry["opposite"]))
        for name, lon in points.items():
            if name in (entry["a"], entry["b"]):
                continue
            for kind, target in targets:
                distance = angular_distance(lon, target)
                if distance <= limit:
                    sign, degree = sign_from_longitude(target)
                    result.append({
                        "pair": entry["pair"],
                        "a": entry["a"],
                        "b": entry["b"],
                        "planet": name,
                        "kind": kind,
                        "midpoint": round(target, 6),
                        "planet_longitude": round(lon, 6),
                        "orb": round(distance, 6),
                        "sign": sign,
                        "degree_in_sign": round(degree, 6),
                        "dial90": round(dial90(target), 6),
                    })
    result.sort(key=lambda item: (item["orb"], item["pair"]))
    return result


def format_picture(entry):
    """Строка вида Солнце/Луна = Марс (орб 0°12')."""
    minutes = int(round(float(entry["orb"]) * 60))
    return (f"{get_planet_name_ru(entry['a'])}/{get_planet_name_ru(entry['b'])} = "
            f"{get_planet_name_ru(entry['planet'])} (орб {minutes}')")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Средние точки и планетарные картины")
    parser.add_argument("--orb", type=float, default=DEFAULT_MIDPOINT_ORB)
    parser.add_argument("--all", action="store_true", help="показать все пары")
    args = parser.parse_args(argv)

    from .chart import build_natal_chart
    birth = {"name": "Demo", "date": "1990-05-15", "time": "14:30",
             "latitude": 55.7558, "longitude": 37.6173, "utc_offset_hours": 3}
    chart = build_natal_chart(birth, {})
    objects = chart["objects"]
    pairs = all_midpoints(objects)
    print(f"Объектов: {len(objects)}; пар средних точек: {len(pairs)}")
    print("=" * 74)
    pictures = occupied_midpoints(objects, orb=args.orb)
    print(f"Занятые средние точки (орб {args.orb}°): {len(pictures)}")
    for entry in pictures[:40]:
        print(f"  {format_picture(entry):<44} "
              f"{entry['degree_in_sign']:5.2f}° {get_sign_name_ru(entry['sign'])}")
    if args.all:
        print("-" * 74)
        for entry in pairs[:60]:
            print(f"  {entry['pair']:<24} {entry['midpoint']:8.3f}°  "
                  f"дайал90 {entry['dial90']:6.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
