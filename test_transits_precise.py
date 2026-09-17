import pytest
from datetime import datetime

from astro_core.transits import (
    normalize_diff,
    get_aspect_target_longitudes,
    find_transit_events,
)
from astro_core.time_service import jd_to_datetime
from astro_core.chart import build_natal_chart
from astro_core.ephemeris import SWISSEPH_AVAILABLE


def test_normalize_diff():
    """Проверка нормализации разницы углов к диапазону [-180, 180)."""
    assert normalize_diff(0) == 0
    assert normalize_diff(90) == 90
    assert normalize_diff(180) == -180
    assert normalize_diff(270) == -90
    assert normalize_diff(360) == 0
    assert normalize_diff(-90) == -90
    assert normalize_diff(-180) == -180
    assert normalize_diff(450) == 90


def test_get_aspect_target_longitudes_conjunction():
    """Проверка целевых долгот для соединения (0°)."""
    targets = get_aspect_target_longitudes(100.0, 0)
    assert len(targets) == 1
    assert abs(targets[0] - 100.0) < 1e-9


def test_get_aspect_target_longitudes_opposition():
    """Проверка целевых долгот для оппозиции (180°)."""
    targets = get_aspect_target_longitudes(100.0, 180)
    assert len(targets) == 1
    assert abs(targets[0] - 280.0) < 1e-9


def test_get_aspect_target_longitudes_square():
    """Проверка целевых долгот для квадрата (90°)."""
    targets = get_aspect_target_longitudes(100.0, 90)
    assert len(targets) == 2
    # Одна цель: 100 + 90 = 190, другая: 100 - 90 = 10
    assert abs(targets[0] - 190.0) < 1e-9
    assert abs(targets[1] - 10.0) < 1e-9


def test_get_aspect_target_longitudes_trine():
    """Проверка целевых долгот для трина (120°)."""
    targets = get_aspect_target_longitudes(100.0, 120)
    assert len(targets) == 2
    # Одна цель: 100 + 120 = 220, другая: 100 - 120 = -20 = 340
    assert abs(targets[0] - 220.0) < 1e-9
    assert abs(targets[1] - 340.0) < 1e-9


def test_jd_to_datetime_j2000():
    """Проверка преобразования Julian Day в datetime для J2000."""
    # J2000 = 2000-01-01 12:00:00 UTC = JD 2451545.0
    dt = jd_to_datetime(2451545.0)
    assert dt.year == 2000
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 12
    assert dt.minute == 0
    assert dt.second == 0


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_find_transit_events():
    """Проверка поиска событий транзитов за период."""
    birth = {
        "name": "Test",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }
    natal_settings = {"include_chiron": False, "include_nodes": False}
    natal = build_natal_chart(birth, natal_settings)

    # Ищем события за 3 дня вокруг даты натала
    events = find_transit_events(
        natal["objects"],
        "1990-05-14",
        "1990-05-16",
    )

    assert len(events) > 0

    # Проверяем структуру каждого события
    for event in events:
        assert "transit_planet" in event
        assert "natal_point" in event
        assert "aspect" in event
        assert "exact_jd" in event
        assert "exact_datetime" in event
        assert "direction" in event
        assert event["direction"] in ("direct", "retrograde")

    # Проверяем, что события отсортированы по дате
    for i in range(len(events) - 1):
        assert events[i]["exact_jd"] <= events[i + 1]["exact_jd"]


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_sun_conjunction_natal_sun():
    """Проверка, что соединение Солнца с натальным Солнцем находится около даты натала."""
    birth = {
        "name": "Test",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }
    natal_settings = {"include_chiron": False, "include_nodes": False}
    natal = build_natal_chart(birth, natal_settings)

    # Ищем события за 3 дня вокруг даты натала
    events = find_transit_events(
        natal["objects"],
        "1990-05-14",
        "1990-05-16",
    )

    # Находим соединение Солнца с натальным Солнцем
    sun_conjunctions = [
        e for e in events
        if e["transit_planet"] == "Sun"
        and e["natal_point"] == "Sun"
        and e["aspect"] == "conjunction"
    ]

    # Должно быть хотя бы одно соединение
    assert len(sun_conjunctions) > 0

    # Проверяем, что соединение произошло около 15 мая 1990
    for event in sun_conjunctions:
        dt = datetime.fromisoformat(event["exact_datetime"])
        assert dt.year == 1990
        assert dt.month == 5
        assert 14 <= dt.day <= 16