"""
Тесты интеграции профилей отображения с транзитами и прогрессиями (шаг 2.5).

Проверяют сквозное поведение: планеты, включённые в профиль, используются
и в натальной карте, и в транзитах, и в прогрессиях.
"""

from datetime import datetime

import pytest

from astro_core.ephemeris import SWISSEPH_AVAILABLE
from astro_core.time_service import datetime_to_jd
from astro_core.transits import calculate_transit_positions, get_transit_calendar
from astro_core.progressions import calculate_secondary_progressions


DEMO_BIRTH = {
    "name": "Demo Person",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
}

pytestmark = pytest.mark.skipif(
    not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed"
)


def test_transit_positions_respect_transit_planets():
    """calculate_transit_positions возвращает только планеты из transit_planets."""
    jd = datetime_to_jd(datetime(2026, 10, 1, 12, 0, 0))
    settings = {"transit_planets": ["Sun", "Moon"]}
    positions, warnings = calculate_transit_positions(jd, settings)
    names = {p["name"] for p in positions}
    assert names == {"Sun", "Moon"}


def test_transit_calendar_respects_transit_planets():
    """Календарь транзитов содержит только включённые транзитные планеты."""
    natal_objects = [
        {"name": "Sun", "longitude": 54.0},
    ]
    settings = {"transit_planets": ["Moon"]}
    calendar = get_transit_calendar(natal_objects, "2026-10-01", "2026-10-30", settings)
    assert len(calendar) > 0, "За 30 дней Луна должна сделать аспекты к Солнцу"
    for entry in calendar:
        assert entry["transit_planet"] == "Moon"


def test_secondary_progressions_respect_enabled_planets():
    """Вторичные прогрессии учитывают enabled_planets из настроек."""
    settings = {"enabled_planets": ["Sun", "Moon", "Mercury"]}
    result = calculate_secondary_progressions(DEMO_BIRTH, "2026-10-01", settings)
    planet_names = {p["name"] for p in result["planets"] if p.get("type") == "planet"}
    assert planet_names == {"Sun", "Moon", "Mercury"}