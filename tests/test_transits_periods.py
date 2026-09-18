import pytest
from datetime import datetime

from astro_core.transits import (
    find_transit_events,
    find_transit_periods,
    get_transit_calendar,
)
from astro_core.chart import build_natal_chart
from astro_core.ephemeris import SWISSEPH_AVAILABLE


@pytest.fixture
def natal_chart():
    """Фикстура: создаёт натальную карту один раз для всех тестов."""
    birth = {
        "name": "Test",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }
    natal_settings = {"include_chiron": False, "include_nodes": False}
    return build_natal_chart(birth, natal_settings)


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_find_transit_periods_basic(natal_chart):
    """Проверка базового поиска периодов активности."""
    periods = find_transit_periods(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
    )

    assert len(periods) > 0

    # Проверяем структуру каждого периода
    for period in periods:
        assert "transit_planet" in period
        assert "natal_point" in period
        assert "aspect" in period
        assert "start_jd" in period
        assert "start_datetime" in period
        assert "exact_jd" in period
        assert "exact_datetime" in period
        assert "end_jd" in period
        assert "end_datetime" in period
        assert "orb" in period
        assert "direction" in period


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_period_start_before_exact_before_end(natal_chart):
    """Проверка логики: вход в орб <= пик <= выход из орба."""
    periods = find_transit_periods(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
    )

    for period in periods:
        assert period["start_jd"] <= period["exact_jd"]
        assert period["exact_jd"] <= period["end_jd"]


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_filter_by_planets(natal_chart):
    """Проверка фильтрации по транзитным планетам."""
    events_all = find_transit_events(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
    )

    events_sun = find_transit_events(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
        filter_planets=["Sun"],
    )

    # Событий с фильтром должно быть меньше или равно общему числу
    assert len(events_sun) <= len(events_all)

    # Все события с фильтром должны быть только про Солнце
    for event in events_sun:
        assert event["transit_planet"] == "Sun"


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_filter_by_aspects(natal_chart):
    """Проверка фильтрации по аспектам."""
    events_conjunction = find_transit_events(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
        filter_aspects=["conjunction"],
    )

    # Все события должны быть только соединениями
    for event in events_conjunction:
        assert event["aspect"] == "conjunction"


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_combined_filter(natal_chart):
    """Проверка комбинированной фильтрации: планеты + аспекты."""
    events = find_transit_events(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
        filter_planets=["Sun"],
        filter_aspects=["conjunction"],
    )

    for event in events:
        assert event["transit_planet"] == "Sun"
        assert event["aspect"] == "conjunction"


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_filter_applied_to_periods(natal_chart):
    """Проверка, что фильтрация работает и для периодов активности."""
    periods = find_transit_periods(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
        filter_planets=["Sun"],
    )

    for period in periods:
        assert period["transit_planet"] == "Sun"


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_filter_applied_to_calendar(natal_chart):
    """Проверка, что фильтрация работает и для календаря по дням."""
    calendar = get_transit_calendar(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
        filter_aspects=["conjunction"],
    )

    for entry in calendar:
        assert entry["aspect"] == "conjunction"


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_empty_filter_returns_all(natal_chart):
    """Проверка, что пустой фильтр (None) возвращает все события."""
    events_all = find_transit_events(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
    )

    events_empty_filter = find_transit_events(
        natal_chart["objects"],
        "1990-05-14",
        "1990-05-16",
        filter_planets=None,
        filter_aspects=None,
    )

    assert len(events_all) == len(events_empty_filter)