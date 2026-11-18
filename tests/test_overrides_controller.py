"""Приоритет галочек над профилем на реальном пути приложения (ChartController)."""
import pytest

from astro_core.controllers import ChartController
from astro_core.ephemeris import ASTEROID_NAMES

BIRTH = {
    "name": "OverridePath", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}
POINTS = ("CrossOfFate", "BlackMoon", "Selena", "Proserpina")


def _names(chart):
    return {o["name"] for o in chart["objects"]}


def test_controller_applies_overrides_over_profile():
    controller = ChartController()
    settings = {"object_overrides": {
        "include_asteroids": True,
        "include_part_of_fortune": False,
        "include_cross_of_fate": False,
        "include_black_moon": False,
        "include_selena": False,
        "include_proserpina": False,
    }}
    chart = controller.calculate_chart(BIRTH, settings, "full", include_svg=False)
    names = _names(chart)
    assert set(ASTEROID_NAMES) <= names, "галочка астероидов должна побеждать профиль"
    assert "PartOfFortune" not in names
    for point in POINTS:
        assert point not in names, f"{point} должен сниматься галочкой"


def test_controller_overrides_can_enable_points():
    controller = ChartController()
    settings = {"object_overrides": {
        "include_asteroids": False,
        "include_part_of_fortune": False,
        "include_cross_of_fate": True,
        "include_black_moon": True,
        "include_selena": True,
        "include_proserpina": True,
    }}
    chart = controller.calculate_chart(BIRTH, settings, "full", include_svg=False)
    names = _names(chart)
    assert not (set(ASTEROID_NAMES) & names)
    assert "PartOfFortune" not in names
    for point in POINTS:
        assert point in names
