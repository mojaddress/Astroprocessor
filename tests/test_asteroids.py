"""Астероиды: расчёт, глифы, цвета, профили, UI и аспекты к углам/точкам."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from astro_core import display_profiles as dp
from astro_core.chart import build_natal_chart
from astro_core.constants import PLANET_NAMES_RU
from astro_core.ephemeris import ASTEROID_NAMES

BIRTH = {
    "name": "AsteroidTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="module")
def chart_with_asteroids():
    return build_natal_chart(BIRTH, {"include_asteroids": True,
                                     "include_part_of_fortune": True,
                                     "include_angles": True})


def test_asteroids_absent_by_default():
    chart = build_natal_chart(BIRTH, {})
    names = {o["name"] for o in chart["objects"]}
    assert not (set(ASTEROID_NAMES) & names)


def test_asteroids_present_when_enabled(chart_with_asteroids):
    names = {o["name"] for o in chart_with_asteroids["planets"]}
    assert set(ASTEROID_NAMES) <= names


def test_asteroid_fields_valid(chart_with_asteroids):
    for obj in chart_with_asteroids["planets"]:
        if obj["name"] in ASTEROID_NAMES:
            assert obj["type"] == "asteroid"
            assert 0.0 <= obj["longitude"] < 360.0
            assert obj["sign"]
            assert isinstance(obj["retrograde"], bool)
            assert obj["house"] in range(1, 13)


def test_asteroids_survive_enabled_planets_filter():
    chart = build_natal_chart(BIRTH, {
        "include_asteroids": True,
        "enabled_planets": ["Sun", "Moon", "Mercury", "Venus", "Mars"],
    })
    names = {o["name"] for o in chart["objects"]}
    assert set(ASTEROID_NAMES) <= names
    assert "Jupiter" not in names


def test_asteroids_in_all_objects(chart_with_asteroids):
    names = {o["name"] for o in chart_with_asteroids["objects"]}
    assert set(ASTEROID_NAMES) <= names


@pytest.mark.parametrize("name", ASTEROID_NAMES)
def test_glyph_exists(name):
    from ui_qt.widgets.astro_glyphs import get_glyph
    glyph = get_glyph(name)
    assert glyph is not None, f"глиф {name} отсутствует - объект не будет нарисован"
    path, fills = glyph
    assert not path.isEmpty()
    rect = path.boundingRect()
    assert 0 <= rect.left() <= rect.right() <= 100
    assert 0 <= rect.top() <= rect.bottom() <= 100


def test_russian_names():
    for name in ASTEROID_NAMES:
        assert PLANET_NAMES_RU.get(name)


def test_colors_defined():
    from ui_qt.widgets.chart_view import PLANET_COLORS
    for name in ASTEROID_NAMES:
        assert name in PLANET_COLORS


def test_full_profile_asteroids_off_by_default():
    for name in dp.BUILTIN_PROFILE_NAMES:
        profile = dp.get_builtin_profile(name)
        assert profile["objects"]["Asteroids"] is False


def test_profile_maps_asteroids_flag():
    profile = dp.get_builtin_profile("full")
    profile["objects"]["Asteroids"] = True
    settings = dp.apply_profile_to_settings(profile, {})
    assert settings["include_asteroids"] is True
    assert dp.validate_profile(profile) == []


def test_ui_checkbox_and_settings(qapp):
    from astro_core.controllers import CityController, ProfileController
    from ui_qt.widgets.birth_input_panel import BirthInputPanel
    panel = BirthInputPanel(CityController(), ProfileController())
    try:
        assert panel.chk_asteroids.isChecked() is False
        assert panel.get_settings()["include_asteroids"] is False
        panel.chk_asteroids.setChecked(True)
        assert panel.get_settings()["include_asteroids"] is True
        panel.set_object_flags({"PartOfFortune": True, "Asteroids": False})
        assert panel.chk_asteroids.isChecked() is False
    finally:
        panel.deleteLater()


def test_draw_angles_returns_positions(qapp, chart_with_asteroids):
    from ui_qt.widgets.chart_view import ChartView
    view = ChartView()
    try:
        view.set_chart_data(chart_with_asteroids, {"show_angle_labels": True})
        positions = view._draw_angles(chart_with_asteroids["additional_points"], 300, 350)
        assert "ASC" in positions and "MC" in positions
    finally:
        view.deleteLater()


def test_draw_points_returns_positions(qapp, chart_with_asteroids):
    from ui_qt.widgets.chart_view import ChartView
    view = ChartView()
    try:
        view.set_chart_data(chart_with_asteroids, {"show_angle_labels": True})
        positions = view._draw_point_of_fortune(
            chart_with_asteroids["additional_points"], 260, 5, 26)
        assert "PartOfFortune" in positions
    finally:
        view.deleteLater()
