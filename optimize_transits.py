"""Ускорение точных транзитов: трек один раз + bisect по дуге + метод Иллинойса.

Запуск:  py -3.11 optimize_transits.py
Патчит:  astro_core/transits.py (backup .bak_transit_fast)
Создаёт: tests/test_transits_fast.py, bench_transits.py, diag_seorbel.py
Идемпотентен: маркер TRANSIT_FAST_V1. Старая реализация сохраняется как legacy.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "astro_core" / "transits.py"
TEST_FILE = ROOT / "tests" / "test_transits_fast.py"
BENCH_FILE = ROOT / "bench_transits.py"
DIAG_FILE = ROOT / "diag_seorbel.py"
MARKER = "TRANSIT_FAST_V1"

IMPORT_ANCHOR = "from datetime import datetime, timedelta"
DEF_ANCHOR = "def find_transit_events(natal_objects, start_date, end_date, settings=None,"
LEGACY_DEF = "def find_transit_events_legacy(natal_objects, start_date, end_date, settings=None,"

NEW_CODE = '''# --- Быстрый поиск точных транзитов --- TRANSIT_FAST_V1
def _build_planet_track(jd_start, jd_end, planet_name, step_days, settings=None, cancel=None):
    """Один проход по периоду: список (jd, longitude, speed).

    Ключевая оптимизация: трек планеты считается один раз, а не заново для
    каждой пары (натальная точка, аспект, целевая долгота).
    """
    track = []
    jd = jd_start
    index = 0
    while jd <= jd_end:
        if cancel is not None and index % 512 == 0:
            cancel()
        lon, speed = get_planet_position(jd, planet_name, settings)
        track.append((jd, lon, speed))
        jd += step_days
        index += 1
    return track


def _refine_crossing_fast(jd_low, jd_high, planet_name, target_longitude, settings=None,
                          tol_deg=1e-9, max_iterations=60):
    """Уточнение пересечения методом Иллинойса (хорда с защитой от застоя).

    Скобка сохраняется, сходимость сверхлинейная: обычно 4-7 обращений
    к эфемеридам вместо ~100 у бинарного поиска.
    """
    lon_low, _ = get_planet_position(jd_low, planet_name, settings)
    f_low = normalize_diff(lon_low - target_longitude)
    lon_high, _ = get_planet_position(jd_high, planet_name, settings)
    f_high = normalize_diff(lon_high - target_longitude)
    if f_low == 0.0:
        return jd_low
    if f_high == 0.0:
        return jd_high
    if (f_low > 0.0) == (f_high > 0.0):
        return (jd_low + jd_high) / 2.0

    jd_mid = (jd_low + jd_high) / 2.0
    side = 0
    for _ in range(max_iterations):
        denominator = f_high - f_low
        if denominator == 0.0:
            jd_mid = (jd_low + jd_high) / 2.0
        else:
            jd_mid = (jd_low * f_high - jd_high * f_low) / denominator
        if not (min(jd_low, jd_high) < jd_mid < max(jd_low, jd_high)):
            jd_mid = (jd_low + jd_high) / 2.0

        lon_mid, _ = get_planet_position(jd_mid, planet_name, settings)
        f_mid = normalize_diff(lon_mid - target_longitude)
        if abs(f_mid) < tol_deg:
            return jd_mid

        if (f_mid > 0.0) == (f_low > 0.0):
            jd_low, f_low = jd_mid, f_mid
            if side == -1:
                f_high *= 0.5
            side = -1
        else:
            jd_high, f_high = jd_mid, f_mid
            if side == 1:
                f_low *= 0.5
            side = 1
    return jd_mid


def _arc_segments(lon_prev, delta):
    """Отрезки внутри [0, 360), покрывающие дугу движения планеты за шаг."""
    lo = lon_prev % 360.0
    hi = lo + delta
    if delta > 0.0:
        if hi <= 360.0:
            return ((lo, hi),)
        return ((lo, 360.0), (0.0, hi - 360.0))
    if hi >= 0.0:
        return ((hi, lo),)
    return ((hi + 360.0, 360.0), (0.0, lo))


def _crossings_from_track(track, targets_sorted, planet_name, settings=None, cancel=None):
    """На каждом шаге трека ищет цели внутри пройденной дуги (bisect)."""
    for index in range(1, len(track)):
        if cancel is not None and index % 1024 == 0:
            cancel()
        jd_prev, lon_prev, _ = track[index - 1]
        jd_curr, lon_curr, _ = track[index]
        delta = normalize_diff(lon_curr - lon_prev)
        if delta == 0.0:
            continue
        for seg_lo, seg_hi in _arc_segments(lon_prev, delta):
            left = bisect_left(targets_sorted, seg_lo)
            right = bisect_left(targets_sorted, seg_hi)
            for k in range(left, right):
                target = targets_sorted[k]
                yield target, _refine_crossing_fast(
                    jd_prev, jd_curr, planet_name, target, settings
                )


def find_transit_events(natal_objects, start_date, end_date, settings=None,
                        filter_planets=None, filter_aspects=None,
                        progress=None, cancel=None):
    """Находит точные моменты транзитных аспектов за период (быстрая версия).

    Контракт и состав событий совпадают с find_transit_events_legacy
    (проверяется тестом эквивалентности). Отличия — только в скорости:
      * трек планеты строится один раз за период;
      * цели ищутся бисекцией по отсортированному списку внутри дуги шага;
      * момент уточняется методом Иллинойса.

    progress(percent, message) и cancel() - необязательные колбэки;
    cancel() может бросить исключение для прерывания расчёта.
    """
    if settings is None:
        settings = DEFAULT_SETTINGS

    enabled_aspects = set(settings.get("enabled_aspects", DEFAULT_SETTINGS.get("enabled_aspects", [])))
    if filter_aspects:
        enabled_aspects = enabled_aspects.intersection(set(filter_aspects))

    transit_planets = settings.get("transit_planets", DEFAULT_TRANSIT_PLANETS)
    if filter_planets:
        transit_planets = [p for p in transit_planets if p in filter_planets]

    start_local, start_utc = parse_local_datetime(start_date, "00:00", 0)
    end_local, end_utc = parse_local_datetime(end_date, "23:59", 0)
    jd_start = datetime_to_jd(start_utc)
    jd_end = datetime_to_jd(end_utc)

    # Цели не зависят от транзитной планеты: строим один раз.
    targets_map = {}
    for natal_obj in natal_objects:
        if "longitude" not in natal_obj or "name" not in natal_obj:
            continue
        for aspect_def in ASPECT_DEFINITIONS:
            aspect_name = aspect_def["name"]
            if aspect_name not in enabled_aspects:
                continue
            for target in get_aspect_target_longitudes(natal_obj["longitude"], aspect_def["angle"]):
                targets_map.setdefault(target, []).append((natal_obj["name"], aspect_name))

    events = []
    if not targets_map or not transit_planets:
        return events

    targets_sorted = sorted(targets_map)
    total = len(transit_planets)

    for index, planet_name in enumerate(transit_planets):
        if cancel is not None:
            cancel()
        step_days = get_step_for_planet(planet_name)
        track = _build_planet_track(jd_start, jd_end, planet_name, step_days, settings, cancel)

        for target, jd in _crossings_from_track(track, targets_sorted, planet_name, settings, cancel):
            _, speed = get_planet_position(jd, planet_name, settings)
            direction = "retrograde" if speed < 0 else "direct"
            exact_dt = jd_to_datetime(jd)
            for natal_name, aspect_name in targets_map[target]:
                events.append({
                    "transit_planet": planet_name,
                    "natal_point": natal_name,
                    "aspect": aspect_name,
                    "target_longitude": round(target, 6),
                    "exact_jd": jd,
                    "exact_datetime": exact_dt.isoformat(),
                    "direction": direction,
                    "orb": 0.0,
                })

        if progress is not None:
            progress(int((index + 1) * 100 / total), f"{planet_name}: событий {len(events)}")

    events.sort(key=lambda e: e["exact_jd"])
    return events


'''

TEST_SRC = '''"""Быстрый поиск транзитов: эквивалентность legacy, дуги, отмена, прогресс."""
import pytest

from astro_core import transits as t
from astro_core.chart import build_natal_chart

BIRTH = {
    "name": "FastTest",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
    "timezone": "Europe/Moscow",
}

needs_swe = pytest.mark.skipif(
    not getattr(t, "calculate_objects", None), reason="ядро недоступно"
)


def _key(event):
    return (event["transit_planet"], event["natal_point"], event["aspect"],
            event["direction"], round(event["target_longitude"], 6))


def test_equivalence_with_legacy_30_days():
    natal = build_natal_chart(BIRTH, {})["objects"]
    legacy = t.find_transit_events_legacy(natal, "2026-01-01", "2026-01-30", {})
    fast = t.find_transit_events(natal, "2026-01-01", "2026-01-30", {})
    assert len(fast) == len(legacy), "количество событий должно совпадать"
    assert sorted(_key(e) for e in fast) == sorted(_key(e) for e in legacy)
    legacy_sorted = sorted(legacy, key=lambda e: (_key(e), e["exact_jd"]))
    fast_sorted = sorted(fast, key=lambda e: (_key(e), e["exact_jd"]))
    for old, new in zip(legacy_sorted, fast_sorted):
        assert abs(old["exact_jd"] - new["exact_jd"]) < 1e-6, "момент должен совпадать до 0.09 с"


def test_empty_natal_returns_empty():
    assert t.find_transit_events([], "2026-01-01", "2026-01-05", {}) == []


def test_filters_respected():
    natal = build_natal_chart(BIRTH, {})["objects"]
    events = t.find_transit_events(
        natal, "2026-01-01", "2026-01-10", {},
        filter_planets=["Moon"], filter_aspects=["conjunction"],
    )
    assert events
    assert {e["transit_planet"] for e in events} == {"Moon"}
    assert {e["aspect"] for e in events} == {"conjunction"}


def test_progress_monotonic_and_finishes_100():
    natal = build_natal_chart(BIRTH, {})["objects"]
    seen = []
    t.find_transit_events(natal, "2026-01-01", "2026-01-05", {},
                          progress=lambda p, m: seen.append(p))
    assert seen and seen[-1] == 100
    assert all(b >= a for a, b in zip(seen, seen[1:]))


def test_cancel_propagates():
    natal = build_natal_chart(BIRTH, {})["objects"]

    def cancel():
        raise RuntimeError("cancelled")

    with pytest.raises(RuntimeError):
        t.find_transit_events(natal, "2026-01-01", "2026-01-30", {}, cancel=cancel)


def test_arc_segments_forward_wrap():
    assert t._arc_segments(359.0, 2.0) == ((359.0, 360.0), (0.0, 1.0))


def test_arc_segments_retrograde_wrap():
    assert t._arc_segments(1.0, -2.0) == ((359.0, 360.0), (0.0, 1.0))


def test_sweep_direct_motion(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position",
                        lambda jd, name, settings=None: (jd % 360.0, 1.0))
    track = [(float(d), float(d % 360), 1.0) for d in range(11)]
    got = list(t._crossings_from_track(track, [5.0], "Sun"))
    assert len(got) == 1
    assert abs(got[0][1] - 5.0) < 1e-6


def test_sweep_wrap_through_zero(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position",
                        lambda jd, name, settings=None: ((350.0 + jd) % 360.0, 1.0))
    track = [(float(d), (350.0 + d) % 360.0, 1.0) for d in range(21)]
    got = dict(t._crossings_from_track(track, [0.0, 355.0], "Sun"))
    assert abs(got[0.0] - 10.0) < 1e-6
    assert abs(got[355.0] - 5.0) < 1e-6


def test_sweep_retrograde_motion(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position",
                        lambda jd, name, settings=None: ((10.0 - jd) % 360.0, -1.0))
    track = [(float(d), (10.0 - d) % 360.0, -1.0) for d in range(11)]
    got = list(t._crossings_from_track(track, [5.0], "Mars"))
    assert len(got) == 1
    assert abs(got[0][1] - 5.0) < 1e-6


def test_sweep_ignores_far_target(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position",
                        lambda jd, name, settings=None: (jd % 360.0, 1.0))
    track = [(float(d), float(d % 360), 1.0) for d in range(11)]
    assert list(t._crossings_from_track(track, [200.0], "Sun")) == []


def test_target_on_sample_counted_once(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position",
                        lambda jd, name, settings=None: (jd % 360.0, 1.0))
    track = [(float(d), float(d % 360), 1.0) for d in range(11)]
    assert len(list(t._crossings_from_track(track, [5.0], "Sun"))) == 1
'''

BENCH_SRC = '''"""Сравнение legacy и быстрого поиска точных транзитов.

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
'''

DIAG_SRC = '''"""Проверка: подхватывает ли Swiss Ephemeris файл seorbel.txt для Селены/Прозерпины.

Запуск: py -3.11 diag_seorbel.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import swisseph as swe

from astro_core.constants import DEFAULT_EPHE_PATH


def main() -> int:
    print("Ожидаемое имя файла (swe.FICTFILE):", repr(getattr(swe, "FICTFILE", "нет константы")))
    print("Путь эфемерид:", DEFAULT_EPHE_PATH)
    folder = Path(DEFAULT_EPHE_PATH)
    print("seorbel.txt на месте:", (folder / "seorbel.txt").exists())
    print("Файлы в ephe:", sorted(p.name for p in folder.glob("seorbel*")))
    swe.set_ephe_path(str(folder))
    jd = 2451545.0
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    for body, name in ((56, "Selena (White Moon)"), (57, "Proserpina")):
        try:
            result = swe.calc_ut(jd, body, flags)
            print(f"{name}: OK  lon={result[0][0]:.6f}  speed={result[0][3]:.6f}")
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: FAIL  {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def main() -> None:
    if not TARGET.exists():
        print(f"[X] Не найден файл {TARGET}")
        sys.exit(1)

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print("[*] Оптимизация уже применена. transits.py не менялся.")
    else:
        if src.count(IMPORT_ANCHOR) != 1 or src.count(DEF_ANCHOR) != 1:
            print("[X] Якоря не найдены однозначно. Файл НЕ изменён.")
            sys.exit(1)
        src = src.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\nfrom bisect import bisect_left", 1)
        src = src.replace(DEF_ANCHOR, LEGACY_DEF, 1)
        src = src.replace(LEGACY_DEF, NEW_CODE + LEGACY_DEF, 1)
        try:
            compile(src, str(TARGET), "exec")
        except SyntaxError as exc:
            print(f"[X] SyntaxError после патча: {exc}. Файл НЕ изменён.")
            sys.exit(1)
        shutil.copy2(TARGET, TARGET.with_name(TARGET.name + ".bak_transit_fast"))
        TARGET.write_text(src, encoding="utf-8")
        print("[+] astro_core/transits.py: быстрый поиск добавлен, старый сохранён как legacy.")

    TEST_FILE.write_text(TEST_SRC, encoding="utf-8")
    print("[+] Создан tests/test_transits_fast.py (12 тестов)")
    BENCH_FILE.write_text(BENCH_SRC, encoding="utf-8")
    print("[+] Создан bench_transits.py")
    DIAG_FILE.write_text(DIAG_SRC, encoding="utf-8")
    print("[+] Создан diag_seorbel.py")

    sys.path.insert(0, str(ROOT))
    try:
        from astro_core import transits as module  # noqa: F401
        assert hasattr(module, "find_transit_events_legacy")
        assert hasattr(module, "_crossings_from_track")
        print("[+] Контроль: legacy и быстрый поиск на месте.")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Ошибка контроля: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()