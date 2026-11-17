"""Гипотеза H-WRAP-1: основная стоимость - обвязка get_planet_position, не эфемериды.

Запуск: py -3.11 bench_wrapper.py
"""
from __future__ import annotations

import sys
import time

from astro_core import ephemeris as e
from astro_core import ephemeris_cache as cache

JD0 = 2451545.0
N = 20000


def measure(label, func):
    start = time.perf_counter()
    for index in range(N):
        func(JD0 + (index % 365))
    ms = (time.perf_counter() - start) * 1000
    per_call = ms * 1000.0 / N
    print(f"{label:<46} {ms:8.1f} мс  {per_call:7.2f} мкс/вызов")
    return per_call


def main() -> int:
    e.initialize_ephemeris({})
    flags, _ = e.setup_zodiac_mode({})
    for index in range(365):
        e.get_planet_position(JD0 + index, "Sun", {})
        cache.calc_ut(JD0 + index, 0, flags)

    print("=" * 84)
    wrapper = measure("get_planet_position (обвязка + кэш)",
                      lambda jd: e.get_planet_position(jd, "Sun", {}))
    raw = measure("ephemeris_cache.calc_ut (только кэш)",
                  lambda jd: cache.calc_ut(jd, 0, flags))
    setup = measure("setup_zodiac_mode (настройки/контекст)",
                    lambda jd: e.setup_zodiac_mode({}))
    print("=" * 84)
    if wrapper > 0:
        print(f"Доля обвязки в стоимости вызова: {(wrapper - raw) / wrapper * 100:.1f}%")
        print(f"setup_zodiac_mode отдельно:      {setup:.2f} мкс (вызывается редко, не на каждый запрос)")
    print("Если обвязка доминирует - следующий выигрыш даёт её упрощение,")
    print("а не дальнейшая оптимизация алгоритмов поиска.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
