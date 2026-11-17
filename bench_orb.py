"""Замер границ орба и проверка гипотезы о нулевых периодах у медленных планет.

Запуск: py -3.11 bench_orb.py
"""
from __future__ import annotations

import sys
import time

from astro_core import transits as t
from astro_core.chart import build_natal_chart

BIRTH = {
    "name": "Bench", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}


def timed(label, func):
    start = time.perf_counter()
    result = func()
    ms = (time.perf_counter() - start) * 1000
    print(f"{label:<48} {ms:9.1f} мс  (записей: {len(result)})")
    return result, ms


def zero_length(periods):
    return sum((1 if p["start_jd"] == p["exact_jd"] else 0) +
               (1 if p["end_jd"] == p["exact_jd"] else 0) for p in periods)


def main() -> int:
    natal = build_natal_chart(BIRTH, {})["objects"]
    print("=" * 84)
    legacy, legacy_ms = timed("Периоды, 30 дней, legacy",
                              lambda: t.find_transit_periods_legacy(
                                  natal, "2026-01-01", "2026-01-30", {}))
    fast, fast_ms = timed("Периоды, 30 дней, быстрые границы",
                          lambda: t.find_transit_periods(
                              natal, "2026-01-01", "2026-01-30", {}))
    print(f"  нулевых периодов: legacy {zero_length(legacy)} из {len(legacy)}"
          f" | новые {zero_length(fast)} из {len(fast)}")
    if fast_ms > 0:
        print(f"  ускорение: {legacy_ms / fast_ms:.1f}x")
    year, year_ms = timed("Периоды, 365 дней, быстрые границы",
                          lambda: t.find_transit_periods(
                              natal, "2026-01-01", "2026-12-31", {}))
    print(f"  нулевых периодов за год: {zero_length(year)} из {len(year)}")
    print("=" * 84)
    print("Гипотеза H-ORB-1: legacy даёт нулевые периоды у медленных планет.")
    print("Если legacy zero > 0, а новые zero = 0 - дефект данных подтверждён и исправлен.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
