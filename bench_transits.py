"""Сравнение legacy и быстрого поиска точных транзитов.

Запуск: py -3.11 bench_transits.py
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
    t0 = time.perf_counter()
    result = func()
    ms = (time.perf_counter() - t0) * 1000
    print(f"{label:<52} {ms:9.1f} мс  (событий: {len(result)})")
    return result, ms


def main() -> int:
    natal = build_natal_chart(BIRTH, {})["objects"]
    print("=" * 80)
    old, old_ms = timed("30 дней, legacy", lambda: t.find_transit_events_legacy(
        natal, "2026-01-01", "2026-01-30", {}))
    new, new_ms = timed("30 дней, быстрый", lambda: t.find_transit_events(
        natal, "2026-01-01", "2026-01-30", {}))
    print(f"  совпадение количества событий: {len(old) == len(new)}")
    if new_ms > 0:
        print(f"  ускорение на 30 днях: {old_ms / new_ms:.1f}x")
    year, year_ms = timed("365 дней, быстрый", lambda: t.find_transit_events(
        natal, "2026-01-01", "2026-12-31", {}))
    print("=" * 80)
    print("Цель: год < 1000 мс. Если достигнуто - фон нужен только для длинных периодов.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
