"""Диагностика: какие тела вызывают исключения Swiss Ephemeris при расчёте натала.

Запуск: py -3.11 diag_ephemeris_errors.py
Ничего не меняет в проекте: временно перехватывает вызовы, печатает отчёт.
"""
from __future__ import annotations

import sys
from collections import Counter

import swisseph as swe

from astro_core.chart import build_natal_chart

BIRTH = {
    "name": "Diag",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
    "timezone": "Europe/Moscow",
}

NAMES = {
    0: "Sun", 1: "Moon", 2: "Mercury", 3: "Venus", 4: "Mars", 5: "Jupiter",
    6: "Saturn", 7: "Uranus", 8: "Neptune", 9: "Pluto", 10: "MeanNode",
    11: "TrueNode", 12: "MeanApog (Lilith)", 13: "OscuApog", 14: "Earth",
    15: "Chiron", 16: "Pholus", 17: "Ceres", 18: "Pallas", 19: "Juno",
    20: "Vesta",
}

failures: Counter = Counter()
original = swe.calc_ut


def traced(jd, body, flags=258, *args, **kwargs):
    try:
        return original(jd, body, flags, *args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        failures[(int(body), str(exc)[:90])] += 1
        raise


def main() -> int:
    swe.calc_ut = traced
    try:
        build_natal_chart(BIRTH, {})
    finally:
        swe.calc_ut = original
    print("=" * 70)
    if not failures:
        print("Исключений Swiss Ephemeris нет - источник errors в статистике иной.")
        return 0
    print("Тела, вызывающие исключения (id, название, текст,количество:):")
    for (body, text), count in failures.most_common():
        name = NAMES.get(body, f"body#{body}")
        print(f"  id={body:<4} {name:<22} x{count:<3} {text}")
    print("=" * 70)
    print("Если это астероиды/Хирон - вероятно, в ephe/ нет файлов seas_*.se1.")
    print("Если это гипотетические точки - их нужно считать геометрически, без swe.calc_ut.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
