"""Решающее измерение: точность границ орба legacy против нового алгоритма.

Запуск: py -3.11 diag_orb_accuracy.py
Проверяет две гипотезы:
  H-ORB-1 (нулевые периоды у медленных планет) - ранее не подтвердилась;
  H-ORB-2 (legacy смещает границы наружу из-за ошибки выбора конца скобки).
"""
from __future__ import annotations

import sys
import time

from astro_core import transits as t
from astro_core.chart import build_natal_chart

BIRTH = {
    "name": "Diag", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}

GROUPS = [
    ("быстрые", ["Sun", "Moon", "Mercury", "Venus", "Mars"], "2026-01-01", "2026-03-31"),
    ("медленные", ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"], "2026-01-01", "2026-12-31"),
]


def stats(periods):
    broken_start = sum(1 for p in periods if p["start_jd"] == p["exact_jd"])
    broken_end = sum(1 for p in periods if p["end_jd"] == p["exact_jd"])
    errors = []
    for period in periods:
        for key in ("start_jd", "end_jd"):
            if period[key] == period["exact_jd"]:
                continue
            lon, _ = t.get_planet_position(period[key], period["transit_planet"], {})
            distance = abs(t.normalize_diff(lon - period["target_longitude"]))
            errors.append(abs(distance - period["orb"]))
    worst = max(errors) if errors else 0.0
    mean = sum(errors) / len(errors) if errors else 0.0
    return broken_start, broken_end, worst, mean


def main() -> int:
    natal = build_natal_chart(BIRTH, {})["objects"]
    print("=" * 92)
    for label, planets, start, end in GROUPS:
        print(f"Группа: {label} ({start} .. {end})")
        for name, func in (("legacy", t.find_transit_periods_legacy),
                           ("новый ", t.find_transit_periods)):
            begin = time.perf_counter()
            periods = func(natal, start, end, {}, filter_planets=planets)
            ms = (time.perf_counter() - begin) * 1000
            bs, be, worst, mean = stats(periods)
            print(f"  {name}: периодов {len(periods):5d} | {ms:8.1f} мс | "
                  f"граница не найдена: назад {bs}, вперёд {be} | "
                  f"ошибка орба: макс {worst:.6f}°, сред {mean:.6f}°")
        print("-" * 92)
    print("H-ORB-2 подтверждается, если у legacy ошибка орба заметно больше нуля,")
    print("а у нового алгоритма она порядка 1e-9°. Это и есть исправленный дефект.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
