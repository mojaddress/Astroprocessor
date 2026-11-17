"""Границы орба: корректность нового алгоритма и сохранение набора событий."""
import pytest

from astro_core import transits as t
from astro_core.chart import build_natal_chart

BIRTH = {
    "name": "OrbTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}

FAST = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
SLOW = ["Jupiter", "Saturn"]


def _linear(jd, name, settings=None):
    return (jd % 360.0, 1.0)


def _boundary_error(period, key):
    lon, _ = t.get_planet_position(period[key], period["transit_planet"], {})
    distance = abs(t.normalize_diff(lon - period["target_longitude"]))
    return abs(distance - period["orb"])


def test_boundary_forward_linear(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position", _linear)
    assert abs(t.find_orb_boundary(10.0, "Sun", 10.0, 5.0, direction="forward") - 15.0) < 1e-6


def test_boundary_backward_linear(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position", _linear)
    assert abs(t.find_orb_boundary(10.0, "Sun", 10.0, 5.0, direction="backward") - 5.0) < 1e-6


def test_zero_orb_returns_exact(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position", _linear)
    assert t.find_orb_boundary(10.0, "Sun", 10.0, 0.0) == 10.0


def test_unfound_boundary_is_reported(monkeypatch):
    monkeypatch.setattr(t, "get_planet_position", lambda jd, name, settings=None: (10.0, 0.0))
    diag = []
    result = t.find_orb_boundary(10.0, "Sun", 10.0, 5.0, direction="forward",
                                 max_days=5.0, diagnostics=diag)
    assert result == 10.0
    assert len(diag) == 1
    assert diag[0]["planet"] == "Sun"


def test_periods_same_event_set_as_legacy():
    """Набор периодов не изменился; границы могут отличаться - legacy неточен."""
    natal = build_natal_chart(BIRTH, {})["objects"]
    legacy = t.find_transit_periods_legacy(natal, "2026-01-01", "2026-01-15", {},
                                           filter_planets=FAST)
    fast = t.find_transit_periods(natal, "2026-01-01", "2026-01-15", {},
                                  filter_planets=FAST)
    assert len(fast) == len(legacy)

    def key(p):
        return (p["transit_planet"], p["natal_point"], p["aspect"], round(p["exact_jd"], 6))

    assert sorted(key(p) for p in fast) == sorted(key(p) for p in legacy)


def test_fast_planet_boundaries_are_accurate():
    natal = build_natal_chart(BIRTH, {})["objects"]
    periods = t.find_transit_periods(natal, "2026-01-01", "2026-01-15", {},
                                     filter_planets=FAST)
    assert periods
    for period in periods:
        assert period["start_jd"] < period["exact_jd"] < period["end_jd"]
        assert _boundary_error(period, "start_jd") < 1e-6
        assert _boundary_error(period, "end_jd") < 1e-6


def test_slow_planets_have_real_accurate_periods():
    natal = build_natal_chart(BIRTH, {})["objects"]
    periods = t.find_transit_periods(natal, "2026-01-01", "2026-01-31", {},
                                     filter_planets=SLOW)
    assert periods
    real = [p for p in periods if p["start_jd"] < p["exact_jd"] < p["end_jd"]]
    assert len(real) >= int(len(periods) * 0.9)
    for period in real:
        assert _boundary_error(period, "start_jd") < 1e-6
        assert _boundary_error(period, "end_jd") < 1e-6


def test_periods_progress_reaches_100():
    natal = build_natal_chart(BIRTH, {})["objects"]
    seen = []
    t.find_transit_periods(natal, "2026-01-01", "2026-01-05", {},
                           progress=lambda p, m: seen.append(p))
    assert seen and seen[-1] == 100


def test_periods_cancel_propagates():
    natal = build_natal_chart(BIRTH, {})["objects"]

    def cancel():
        raise RuntimeError("cancelled")

    with pytest.raises(RuntimeError):
        t.find_transit_periods(natal, "2026-01-01", "2026-01-10", {}, cancel=cancel)
