"""Сквозной замер: где реально уходит время (ядро, не микровызовы эфемерид).

Запуск: py -3.11 bench_chart.py
"""
from __future__ import annotations

import sys
import time

from astro_core import ephemeris_cache as cache
from astro_core.chart import build_natal_chart
from astro_core.transits import get_transit_calendar

BIRTH = {
    "name": "Bench",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
    "timezone": "Europe/Moscow",
}


def timed(label, func, repeat=1):
    best = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        result = func()
        ms = (time.perf_counter() - t0) * 1000
        best = ms if best is None else min(best, ms)
    print(f"{label:<44} {best:9.1f} мс")
    return result


def main() -> int:
    print("=" * 66)
    cache.clear()
    cache.reset_stats()
    natal = timed("Натальная карта, холодный расчёт", lambda: build_natal_chart(BIRTH, {}))
    timed("Натальная карта, тёплый расчёт", lambda: build_natal_chart(BIRTH, {}), repeat=3)
    print(f"  кэш после натала: {cache.stats()}")

    objects = natal["objects"]
    for days, (start, end) in (
        (30, ("2026-01-01", "2026-01-30")),
        (365, ("2026-01-01", "2026-12-31")),
    ):
        cache.reset_stats()
        timed(
            f"Календарь транзитов, {days} дней (холодный)",
            lambda s=start, e=end: get_transit_calendar(objects, s, e, {}),
        )
        timed(
            f"Календарь транзитов, {days} дней (тёплый)",
            lambda s=start, e=end: get_transit_calendar(objects, s, e, {}),
            repeat=2,
        )
        print(f"  кэш после {days} дней: {cache.stats()}")
    print("=" * 66)
    print("Если тёплый календарь почти не быстрее холодного - узкое место")
    print("в логике аспектов/агрегации, а не в эфемеридах. Следующий шаг: фон (QThread)")
    print("и оптимизация расчёта аспектов, а не дальнейший кэш эфемерид.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
