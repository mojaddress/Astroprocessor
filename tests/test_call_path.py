"""Кэш контекста эфемерид, мемоизация id планет, останов уточнения по времени."""
import pytest

from astro_core import ephemeris as e
from astro_core import ephemeris_cache as cache
from astro_core import transits as t

JD = 2451545.0


@pytest.fixture(autouse=True)
def _reset_context():
    e._ACTIVE_CONTEXT = None
    cache.clear()
    yield
    e._ACTIVE_CONTEXT = None


def test_context_configured_once_for_same_settings(monkeypatch):
    calls = []
    original = e.setup_zodiac_mode

    def counted(settings):
        calls.append(1)
        return original(settings)

    monkeypatch.setattr(e, "setup_zodiac_mode", counted)
    e.get_planet_position(JD, "Sun", {})
    e.get_planet_position(JD + 1, "Sun", {})
    e.get_planet_position(JD + 2, "Moon", {})
    assert len(calls) == 1, "контекст не должен пересчитываться на каждый вызов"


def test_zodiac_switch_changes_result():
    tropical = e.get_planet_position(JD, "Sun", {"zodiac": "tropical"})
    sidereal = e.get_planet_position(JD, "Sun", {"zodiac": "sidereal", "ayanamsha": "lahiri"})
    assert abs(tropical[0] - sidereal[0]) > 1.0, "сидерический режим обязан менять долготу"
    back = e.get_planet_position(JD, "Sun", {"zodiac": "tropical"})
    assert abs(back[0] - tropical[0]) < 1e-9, "возврат к тропическому должен быть точным"


def test_position_matches_direct_cache():
    flags, _ = e._ensure_context({})
    lon, speed = e.get_planet_position(JD, "Sun", {})
    coords = cache.calc_ut(JD, e.get_planet_id("Sun"), flags)[0]
    assert abs(lon - e.normalize_longitude(float(coords[0]))) < 1e-12
    assert abs(speed - float(coords[3])) < 1e-12


def test_planet_id_memoized_and_correct():
    assert e.get_planet_id("Sun") == 0
    assert e.get_planet_id("Moon") == 1
    assert e.get_planet_id("Sun") == 0


def test_unknown_planet_still_raises():
    with pytest.raises(ValueError):
        e.get_planet_id("NoSuchBody")


def test_warnings_survive_cached_context():
    settings = {"zodiac": "sidereal", "ayanamsha": "unknown_system"}
    _, first = e.calculate_objects(JD, settings)
    _, second = e.calculate_objects(JD, settings)
    assert first and first == second, "предупреждения не должны теряться на кэшированном пути"


def test_orb_refinement_stops_early(monkeypatch):
    calls = []

    def fake(jd, name, settings=None):
        calls.append(jd)
        return (jd % 360.0, 1.0)

    monkeypatch.setattr(t, "get_planet_position", fake)
    boundary = t.find_orb_boundary(10.0, "Sun", 10.0, 5.0, direction="forward")
    assert abs(boundary - 15.0) < 1e-6
    assert len(calls) < 25, "уточнение не должно сжигать все итерации"


def test_crossing_refinement_stops_early(monkeypatch):
    calls = []

    def fake(jd, name, settings=None):
        calls.append(jd)
        return (jd % 360.0, 1.0)

    monkeypatch.setattr(t, "get_planet_position", fake)
    result = t._refine_crossing_fast(0.0, 10.0, "Sun", 5.0)
    assert abs(result - 5.0) < 1e-6
    assert len(calls) < 25
