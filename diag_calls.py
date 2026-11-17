"""Сколько обращений к эфемеридам реально делают тяжёлые режимы.

Запуск: py -3.11 diag_calls.py
Проверяет H-TOL-1: до допуска по времени уточнение сжигало все 60 итераций.
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


def counted_run(label, func):
    original = t.get_planet_position
    counter = [0]

    def wrapper(jd, name, settings=None):
        counter[0] += 1
        return original(jd, name, settings)

    t.get_planet_position = wrapper
    start = time.perf_counter()
    try:
        result = func()
    finally:
        t.get_planet_position = original
    ms = (time.perf_counter() - start) * 1000
    items = len(result) if hasattr(result, "__len__") else 0
    per_item = counter[0] / items if items else 0
    print(f"{label:<40} {ms:8.1f} мс | вызовов {counter[0]:8d} | "
          f"записей {items:6d} | вызовов/запись {per_item:7.1f}")


def main() -> int:
    natal = build_natal_chart(BIRTH, {})["objects"]
    print("=" * 92)
    counted_run("Точные транзиты, год",
                lambda: t.find_transit_events(natal, "2026-01-01", "2026-12-31", {}))
    counted_run("Периоды активности, год",
                lambda: t.find_transit_periods(natal, "2026-01-01", "2026-12-31", {}))
    print("=" * 92)
    print("Ориентир: до патча уточнение делало до 60 итераций на событие/границу.")
    print("После патча ожидается единицы вызовов на уточнение.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
