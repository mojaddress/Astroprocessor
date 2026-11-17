"""Замер режима «Периоды активности» и мультигодовых точных транзитов.

Запуск: py -3.11 bench_periods.py
Решение о фоновом потоке принимается по этим числам (порог ~200 мс).
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
    count = len(result) if hasattr(result, "__len__") else "-"
    flag = "ФОН НУЖЕН" if ms > 200 else "синхронно допустимо"
    print(f"{label:<46} {ms:9.1f} мс  (записей: {count})  {flag}")
    return result


def main() -> int:
    natal = build_natal_chart(BIRTH, {})["objects"]
    print("=" * 88)
    timed("Периоды активности, 30 дней",
          lambda: t.find_transit_periods(natal, "2026-01-01", "2026-01-30", {}))
    timed("Периоды активности, 365 дней",
          lambda: t.find_transit_periods(natal, "2026-01-01", "2026-12-31", {}))
    timed("Точные транзиты, 5 лет",
          lambda: t.find_transit_events(natal, "2026-01-01", "2030-12-31", {}))
    print("=" * 88)
    print("Порог 200 мс: выше - операция уходит в фон с прогрессом и отменой.")
    return 0


if __name__ == "__main__":
    sys.exit(main())