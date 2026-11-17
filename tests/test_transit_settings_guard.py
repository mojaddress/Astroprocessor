"""Регрессия: None в настройках транзитов не должен ронять расчёт."""
import pytest

from astro_core import transits as t
from astro_core.chart import build_natal_chart
from astro_core.controllers import TransitController

BIRTH = {
    "name": "GuardTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}

NONE_SETTINGS = {"enabled_aspects": None, "orbs": None, "transit_planets": None}


@pytest.fixture(scope="module")
def natal():
    return build_natal_chart(BIRTH, {})["objects"]


def test_precise_with_none_values(natal):
    events = t.find_transit_events(natal, "2026-01-01", "2026-01-03", NONE_SETTINGS)
    assert events, "None должен трактоваться как «по умолчанию»"


def test_calendar_with_none_values(natal):
    result = t.get_transit_calendar(natal, "2026-01-01", "2026-01-03", NONE_SETTINGS)
    assert isinstance(result, list)


def test_periods_with_none_values(natal):
    result = t.find_transit_periods(natal, "2026-01-01", "2026-01-03", NONE_SETTINGS)
    assert isinstance(result, list)


def test_explicit_empty_aspects_means_no_aspects(natal):
    """Пустой список - явный запрет аспектов, его нельзя подменять дефолтом."""
    assert t.find_transit_events(natal, "2026-01-01", "2026-01-05",
                                 {"enabled_aspects": []}) == []


def test_controller_without_display_profile(natal):
    """Путь, который в приложении маскировался профилем отображения."""
    controller = TransitController()
    result = controller.calculate_transits(
        natal, "2026-01-01", "2026-01-03",
        controller.get_default_settings(), mode="precise")
    assert isinstance(result, list)
