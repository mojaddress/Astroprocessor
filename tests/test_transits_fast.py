"""Быстрый поиск транзитов: эквивалентность legacy, дуги, отмена, прогресс."""
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
