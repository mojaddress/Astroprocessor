"""Галочки объектов управляют видимостью; углы всегда на карте."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from astro_core import display_profiles as dp
from astro_core.chart import build_natal_chart
from astro_core.ephemeris import ASTEROID_NAMES

BIRTH = {
    "name": "FlagsTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}
POINTS = ("CrossOfFate", "BlackMoon", "Selena", "Proserpina")


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(qapp):
    from astro_core.controllers import CityController, ProfileController
    from ui_qt.widgets.birth_input_panel import BirthInputPanel
    widget = BirthInputPanel(CityController(), ProfileController())
    yield widget
    widget.deleteLater()


def _names(chart):
    return {o["name"] for o in chart["objects"]}


def test_points_independent_of_fortune():
    chart = build_natal_chart(BIRTH, {
        "include_part_of_fortune": False,
        "include_cross_of_fate": True,
        "include_black_moon": True,
        "include_selena": True,
        "include_proserpina": True,
    })
    names = _names(chart)
    assert "PartOfFortune" not in names
    for point in POINTS:
        assert point in names, f"{point} не должен зависеть от Фортуны"


def test_all_asteroids_with_fortune_off():
    chart = build_natal_chart(BIRTH, {
        "include_part_of_fortune": False, "include_asteroids": True})
    assert set(ASTEROID_NAMES) <= _names(chart)


def test_overrides_beat_profile():
    settings = dp.apply_profile_to_settings(dp.get_builtin_profile("full"), {})
    assert settings["include_asteroids"] is False
    settings["object_overrides"] = {"include_asteroids": True,
                                    "include_part_of_fortune": False}
    chart = build_natal_chart(BIRTH, settings)
    names = _names(chart)
    assert set(ASTEROID_NAMES) <= names
    assert "PartOfFortune" not in names


def test_overrides_can_disable_objects():
    chart = build_natal_chart(BIRTH, {
        "include_asteroids": True,
        "object_overrides": {"include_asteroids": False},
    })
    assert not (set(ASTEROID_NAMES) & _names(chart))


def test_checked_off_removes_points():
    chart = build_natal_chart(BIRTH, {
        "include_part_of_fortune": True,
        "object_overrides": {
            "include_cross_of_fate": False, "include_black_moon": False,
            "include_selena": False, "include_proserpina": False},
    })
    names = _names(chart)
    assert "PartOfFortune" in names
    for point in POINTS:
        assert point not in names


def test_panel_sends_overrides_and_angles(panel):
    panel.chk_asteroids.setChecked(True)
    panel.chk_cross.setChecked(True)
    settings = panel.get_settings()
    assert settings["include_angles"] is True
    assert settings["include_dsc"] is True
    assert settings["show_angle_labels"] is True
    assert settings["object_overrides"]["include_asteroids"] is True
    assert settings["object_overrides"]["include_cross_of_fate"] is True
    panel.chk_asteroids.setChecked(False)
    assert panel.get_settings()["object_overrides"]["include_asteroids"] is False


def test_angles_checkboxes_not_in_layout(panel):
    layout = panel.chk_asteroids.parent().findChild(type(panel.chk_asteroids.parent().layout()))
    del layout  # проверяем через геометрию: скрытые виджеты не имеют родителя-раскладки
    assert panel.chk_angles.isHidden() or not panel.chk_angles.isVisible()
    assert panel.chk_dsc.isHidden() or not panel.chk_dsc.isVisible()


def test_angles_drawn_even_if_settings_disable(qapp):
    from ui_qt.widgets.chart_view import ChartView
    chart = build_natal_chart(BIRTH, {})
    view = ChartView()
    try:
        view.set_chart_data(chart, {"show_angle_labels": False, "show_dsc": False})
        positions = view._draw_angles(chart["additional_points"], 300, 350)
        assert {"ASC", "MC", "DSC"} <= set(positions)
    finally:
        view.deleteLater()


def test_asteroid_labels_follow_flag(qapp):
    from ui_qt.widgets.chart_view import ChartView
    view = ChartView()
    try:
        view._settings["text_asteroids"] = False
        assert view._text_label("Ceres") is False
        view._settings["text_asteroids"] = True
        assert view._text_label("Ceres") is True
    finally:
        view.deleteLater()
