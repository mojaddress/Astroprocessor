import pytest

from astro_core.transits import (
    calculate_transit_positions,
    find_transits_on_date,
    get_transit_calendar,
)
from astro_core.chart import build_natal_chart
from astro_core.time_service import parse_local_datetime, datetime_to_jd
from astro_core.ephemeris import SWISSEPH_AVAILABLE


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_calculate_transit_positions():
    """Проверка расчёта транзитных позиций."""
    local_dt, utc_dt = parse_local_datetime("2026-08-18", "12:00", 0)
    jd = datetime_to_jd(utc_dt)

    transit_objects, warnings = calculate_transit_positions(jd)

    # По умолчанию 10 планет (Sun-Pluto), без Хирона и узлов
    assert len(transit_objects) == 10

    # Проверяем структуру каждого объекта
    for obj in transit_objects:
        assert "name" in obj
        assert "longitude" in obj
        assert "sign" in obj
        assert "degree_in_sign" in obj


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_find_transits_on_date():
    """Проверка нахождения транзитов на дату."""
    # Создаём натальную карту
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

    # Используем ту же дату для транзитов.
    # Это гарантирует, что будут соединения планет с самими собой.
    local_dt, utc_dt = parse_local_datetime("1990-05-15", "14:30", 3)
    jd = datetime_to_jd(utc_dt)

    transit_objects, _ = calculate_transit_positions(jd)
    transits = find_transits_on_date(natal["objects"], transit_objects)

    # Должны быть транзиты (как минимум соединения)
    assert len(transits) > 0

    # Проверяем структуру каждого транзита
    for transit in transits:
        assert "transit_planet" in transit
        assert "natal_point" in transit
        assert "aspect" in transit
        assert "orb" in transit
        assert "strength" in transit


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_get_transit_calendar():
    """Проверка календаря транзитов за период."""
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

    # Календарь на 3 дня, начиная с даты натала.
    # Гарантированно будут транзиты.
    calendar = get_transit_calendar(
        natal["objects"],
        "1990-05-15",
        "1990-05-17",
    )

    assert len(calendar) > 0

    # Проверяем структуру каждой записи
    for entry in calendar:
        assert "date" in entry
        assert "transit_planet" in entry
        assert "natal_point" in entry
        assert "aspect" in entry
        assert "orb" in entry


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_transit_calendar_dates_are_valid():
    """Проверка, что даты в календаре находятся в заданном периоде."""
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

    start_date = "1990-05-15"
    end_date = "1990-05-17"

    calendar = get_transit_calendar(
        natal["objects"],
        start_date,
        end_date,
    )

    for entry in calendar:
        assert entry["date"] >= start_date
        assert entry["date"] <= end_date