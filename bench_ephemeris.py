"""Замер эффекта кэша эфемерид на реальной Swiss Ephemeris.

Запуск: py -3.11 bench_ephemeris.py
Печатает: время холодного и тёплого прохода, ускорение, статистику кэша.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from astro_core.ephemeris_cache import DEFAULT_FLAGS, EphemerisCache

DAYS = 365
BODIES = list(range(10))  # Sun..Pluto
JD0 = 2451545.0


def main() -> int:
    try:
        import swisseph as swe
    except ImportError:
        print("[X] pyswisseph не установлен: py -3.11 -m pip install pyswisseph")
        return 1

    ephe = Path(__file__).resolve().parent / "ephe"
    if ephe.exists():
        swe.set_ephe_path(str(ephe))
    flags = DEFAULT_FLAGS
    try:
        swe.calc_ut(JD0, 0, flags)
    except Exception:
        flags = 4 | 256  # FLG_MOSEPH | FLG_SPEED - без файлов эфемерид
        print("[i] Файлы эфемерид недоступны, использую Moshier (точность ниже, замер корректен)")

    cache = EphemerisCache(backend=swe, maxsize=8192, context={"ephe": str(ephe), "flags": flags})

    def raw_pass():
        for d in range(DAYS):
            for b in BODIES:
                swe.calc_ut(JD0 + d, b, flags)

    def cached_pass():
        for d in range(DAYS):
            for b in BODIES:
                cache.calc_ut(JD0 + d, b, flags)

    t0 = time.perf_counter(); raw_pass(); raw_ms = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter(); cached_pass(); cold_ms = (time.perf_counter() - t0) * 1000
    cache.reset_stats()
    t0 = time.perf_counter(); cached_pass(); warm_ms = (time.perf_counter() - t0) * 1000

    calls = DAYS * len(BODIES)
    print("=" * 62)
    print(f"Вызовов на проход: {calls} ({DAYS} дней x {len(BODIES)} тел)")
    print(f"Без кэша (swisseph напрямую): {raw_ms:9.1f} мс")
    print(f"С кэшем, холодный проход:     {cold_ms:9.1f} мс")
    print(f"С кэшем, тёплый проход:       {warm_ms:9.1f} мс")
    if warm_ms > 0:
        print(f"Ускорение тёплого прохода:    {raw_ms / warm_ms:9.1f}x")
    print(f"Статистика кэша: {cache.stats()}")
    print("=" * 62)

    t0 = time.perf_counter()
    for d in range(DAYS):
        swe.houses_ex(JD0 + d, 55.75, 37.61, b"P")
    raw_h = (time.perf_counter() - t0) * 1000
    for _ in range(2):
        t0 = time.perf_counter()
        for d in range(DAYS):
            cache.houses_ex(JD0 + d, 55.75, 37.61, b"P")
        warm_h = (time.perf_counter() - t0) * 1000
    print(f"Дома, без кэша: {raw_h:9.1f} мс | с кэшем (тёплый): {warm_h:9.1f} мс")
    return 0


if __name__ == "__main__":
    sys.exit(main())