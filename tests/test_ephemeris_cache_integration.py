"""Интеграция кэша: эквивалентность, использование, инвалидация по смене состояния."""
import pytest

from astro_core import ephemeris as eph
from astro_core import ephemeris_cache as cache
from astro_core.chart import build_natal_chart

pytestmark = pytest.mark.skipif(
    not eph.SWISSEPH_AVAILABLE, reason="Swiss Ephemeris недоступен"
)

JD = 2451545.0
BIRTH = {
    "name": "CacheTest",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
    "timezone": "Europe/Moscow",
}


@pytest.fixture(autouse=True)
def _fresh():
    eph.initialize_ephemeris({})
    cache.clear()
    cache.reset_stats()
    yield


def test_decorator_forwards_args_and_result():
    @eph._invalidates_ephemeris_cache
    def func(value, extra=None):
        return value * 2, extra

    assert func(3, extra="x") == (6, "x")


def test_decorator_keeps_cache_on_same_state():
    @eph._invalidates_ephemeris_cache
    def func(settings):
        return None

    func({"zodiac": "tropical"})
    cache.calc_ut(JD, 0)
    size_before = cache.size()
    assert size_before > 0
    func({"zodiac": "tropical"})
    assert cache.size() == size_before, "повторный вызов с теми же настройками не должен сбрасывать кэш"


def test_decorator_clears_on_zodiac_change():
    @eph._invalidates_ephemeris_cache
    def func(settings):
        return None

    func({"zodiac": "tropical"})
    cache.calc_ut(JD, 0)
    assert cache.size() > 0
    func({"zodiac": "sidereal", "ayanamsha": "lahiri"})
    assert cache.size() == 0, "смена зодиака обязана сбросить кэш"


def test_decorator_clears_on_ephe_path_change():
    @eph._invalidates_ephemeris_cache
    def func(settings):
        return None

    func({"ephe_path": "ephe"})
    cache.calc_ut(JD, 0)
    assert cache.size() > 0
    func({"ephe_path": "other_ephe"})
    assert cache.size() == 0


def test_calculate_objects_warm_equals_cold_and_uses_cache():
    cold = eph.calculate_objects(JD, {})
    warm = eph.calculate_objects(JD, {})
    assert cold == warm, "кэш не должен менять результаты расчёта"
    assert cache.stats()["hits"] > 0, "кэш должен реально использоваться"


def test_get_planet_position_warm_equals_cold():
    cold = eph.get_planet_position(JD, "Sun", {})
    warm = eph.get_planet_position(JD, "Sun", {})
    assert cold == warm
    assert cache.stats()["hits"] > 0


def test_repeated_natal_charts_use_cache():
    first = build_natal_chart(BIRTH, {})
    second = build_natal_chart(BIRTH, {})
    assert first["objects"] == second["objects"]
    assert cache.stats()["hits"] > 0


def test_houses_still_work_after_integration():
    assert eph.calculate_houses(JD, 55.7558, 37.6173, {}) is not None
