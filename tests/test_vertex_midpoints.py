"""Вертекс и средние точки: расчёт, глифы, планетарные картины, панель."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from astro_core import display_profiles as dp
from astro_core import ephemeris as eph
from astro_core import midpoints as mp
from astro_core.chart import build_natal_chart
from astro_core.constants import PLANET_NAMES_RU

BIRTH = {
    "name": "VxMp", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="module")
def chart():
    return build_natal_chart(BIRTH, {"include_vertex": True})


def _names(data):
    return {o["name"] for o in data["objects"]}


def test_vertex_absent_by_default():
    assert "Vertex" not in _names(build_natal_chart(BIRTH, {}))


def test_vertex_present_when_enabled(chart):
    assert "Vertex" in _names(chart)


def test_vertex_matches_swisseph(chart):
    vertex = next(o for o in chart["objects"] if o["name"] == "Vertex")
    expected = eph.calculate_vertex(chart["julian_day"], BIRTH["latitude"],
                                    BIRTH["longitude"], chart["settings"])
    assert abs(vertex["longitude"] - expected) < 1e-4
    assert 0.0 <= vertex["longitude"] < 360.0
    assert vertex["house"] in range(1, 13)


def test_vertex_glyph_and_names():
    from ui_qt.widgets.astro_glyphs import get_glyph
    from ui_qt.widgets.chart_view import PLANET_COLORS
    glyph = get_glyph("Vertex")
    assert glyph is not None
    path, _fills = glyph
    assert not path.isEmpty()
    assert "Vertex" in PLANET_COLORS
    assert PLANET_NAMES_RU["Vertex"] == "Вертекс"


def test_vertex_opt_in_in_profiles():
    for name in dp.BUILTIN_PROFILE_NAMES:
        profile = dp.get_builtin_profile(name)
        assert profile["objects"]["Vertex"] is False
        assert dp.validate_profile(profile) == []


def test_midpoint_symmetry_and_range():
    for a, b in ((0.0, 90.0), (350.0, 10.0), (180.0, 0.0), (123.4, 300.7)):
        near = mp.midpoint_longitude(a, b)
        assert 0.0 <= near < 360.0
        assert abs(near - mp.midpoint_longitude(b, a)) < 1e-9


def test_midpoint_known_values():
    assert abs(mp.midpoint_longitude(0.0, 90.0) - 45.0) < 1e-9
    assert abs(mp.midpoint_longitude(350.0, 10.0) - 0.0) < 1e-9


def test_all_midpoints_count(chart):
    objects = chart["objects"]
    pairs = mp.all_midpoints(objects)
    n = len({o["name"] for o in objects if o.get("longitude") is not None})
    assert len(pairs) == n * (n - 1) // 2
    for entry in pairs:
        assert 0.0 <= entry["dial90"] < 90.0


def test_occupied_excludes_own_pair(chart):
    for entry in mp.occupied_midpoints(chart["objects"], orb=3.0):
        assert entry["planet"] not in (entry["a"], entry["b"])
        assert entry["orb"] <= 3.0


def test_occupied_sorted_by_orb(chart):
    orbs = [e["orb"] for e in mp.occupied_midpoints(chart["objects"], orb=2.0)]
    assert orbs == sorted(orbs)


def test_occupied_zero_orb_empty(chart):
    assert mp.occupied_midpoints(chart["objects"], orb=0.0) == []


def test_occupied_synthetic():
    objects = [
        {"name": "Sun", "longitude": 0.0},
        {"name": "Moon", "longitude": 90.0},
        {"name": "Mars", "longitude": 45.2},
    ]
    entries = mp.occupied_midpoints(objects, orb=1.0, include_opposite=False)
    assert len(entries) == 1
    assert entries[0]["planet"] == "Mars"
    assert abs(entries[0]["orb"] - 0.2) < 1e-6
    assert "Марс" in mp.format_picture(entries[0])


def test_panel_builds_and_filters(qapp, chart):
    from ui_qt.widgets.midpoints_panel import MidpointsPanel
    panel = MidpointsPanel(lambda: chart)
    try:
        panel.chk_only_occupied.setChecked(False)
        panel._on_calculate()
        all_rows = panel.table.rowCount()
        assert all_rows > 0
        panel.chk_only_occupied.setChecked(True)
        panel.spin_orb.setValue(0.5)
        panel._on_calculate()
        assert panel.table.rowCount() <= all_rows
    finally:
        panel.deleteLater()


def test_panel_without_chart(qapp):
    from ui_qt.widgets.midpoints_panel import MidpointsPanel
    panel = MidpointsPanel(lambda: None)
    try:
        panel._on_calculate()
        assert panel.table.rowCount() == 0
    finally:
        panel.deleteLater()


def test_vertex_checkbox_exists(qapp):
    from astro_core.controllers import CityController, ProfileController
    from ui_qt.widgets.birth_input_panel import BirthInputPanel
    panel = BirthInputPanel(CityController(), ProfileController())
    try:
        assert panel.chk_vertex.isChecked() is False
        panel.chk_vertex.setChecked(True)
        assert panel.get_settings()["object_overrides"]["include_vertex"] is True
    finally:
        panel.deleteLater()


def test_midpoints_tab_exists(qapp):
    from ui_qt.main_window import MainWindow
    window = MainWindow()
    try:
        assert window._calc_tabs.indexOf(window._midpoints_panel) >= 0
    finally:
        window._time_slider.stop()
        window._background.cancel()
        window._background.wait(3000)
        window.deleteLater()
