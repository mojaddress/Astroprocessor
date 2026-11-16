"""Замер долгих операций: точные транзиты и дирекции (нужен ли фоновый поток).

Запуск: py -3.11 bench_long_ops.py
"""
from __future__ import annotations

import sys
import time
from datetime import date

from astro_core import ephemeris_cache as cache
from astro_core.chart import build_natal_chart
from astro_core.directions import calculate_directions
from astro_core.transits import find_transit_events

BIRTH = {
    "name": "Bench",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
    "timezone": "Europe/Moscow",
}


def timed(label, func):
    t0 = time.perf_counter()
    result = func()
    ms = (time.perf_counter() - t0) * 1000
    size = len(result) if hasattr(result, "__len__") else "-"
    print(f"{label:<48} {ms:9.1f} мс  (записей: {size})")
    return result


def main() -> int:
    print("=" * 78)
    natal = build_natal_chart(BIRTH, {})
    objects = natal["objects"]

    for days, (start, end) in (
        (30, ("2026-01-01", "2026-01-30")),
        (365, ("2026-01-01", "2026-12-31")),
    ):
        cache.reset_stats()
        timed(
            f"Точные транзиты, {days} дней (холодный)",
            lambda s=start, e=end: find_transit_events(objects, s, e, {}),
        )
        timed(
            f"Точные транзиты, {days} дней (тёплый)",
            lambda s=start, e=end: find_transit_events(objects, s, e, {}),
        )
        st = cache.stats()
        print(f"  кэш: hits={st['hits']} misses={st['misses']} hit_rate={st['hit_rate']:.2f}")

    timed("Дирекции солнечной дуги на дату", lambda: calculate_directions(natal, date(2026, 11, 13)))
    print("=" * 78)
    print("Порог для фонового потока (QThread): операция дольше ~200 мс.")
    print("Всё, что быстрее, оставляем синхронным - сложность не оправдана.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
