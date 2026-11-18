"""Системы домов: работоспособность каждой, подписи, связь UI и ядра."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from astro_core import ephemeris as eph
from astro_core.constants import HOUSE_SYSTEM_CODES, HOUSE_SYSTEM_NAMES_RU

JD = 2451545.0
LAT = 55.7558
LON = 37.6173


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


@pytest.mark.parametrize("key", sorted(HOUSE_SYSTEM_CODES))
def test_system_produces_twelve_houses(key):
    houses, asc, mc = eph.calculate_houses(JD, LAT, LON, {"house_system": key})
    assert len(houses) == 12, f"{key}: ожидалось 12 домов"
    assert all(0.0 <= h["longitude"] < 360.0 for h in houses)
    assert [h["house"] for h in houses] == list(range(1, 13))
    assert 0.0 <= asc < 360.0
    assert 0.0 <= mc < 360.0


def test_unknown_system_falls_back_to_placidus():
    fallback, asc, mc = eph.calculate_houses(JD, LAT, LON, {"house_system": "no_such"})
    placidus, asc_p, mc_p = eph.calculate_houses(JD, LAT, LON, {"house_system": "placidus"})
    assert [h["longitude"] for h in fallback] == [h["longitude"] for h in placidus]
    assert asc == asc_p and mc == mc_p


def test_every_system_has_russian_name():
    assert set(HOUSE_SYSTEM_NAMES_RU) == set(HOUSE_SYSTEM_CODES)
    assert all(name.strip() for name in HOUSE_SYSTEM_NAMES_RU.values())


def test_codes_are_single_ascii_letters():
    for key, code in HOUSE_SYSTEM_CODES.items():
        assert len(code) == 1 and code.isascii() and code.isalpha(), key


def test_at_least_seventeen_systems():
    assert len(HOUSE_SYSTEM_CODES) >= 17


def test_ui_combo_lists_all_systems(panel):
    keys = {panel.combo_house_system.itemData(i)
            for i in range(panel.combo_house_system.count())}
    assert keys == set(HOUSE_SYSTEM_CODES)
    assert panel.combo_house_system.itemText(0) == HOUSE_SYSTEM_NAMES_RU["placidus"]


def test_ui_settings_return_key_not_label(panel):
    panel.set_house_system("campanus")
    assert panel.get_settings()["house_system"] == "campanus"


def test_ui_set_house_system_ignores_unknown(panel):
    panel.set_house_system("placidus")
    panel.set_house_system("no_such_system")
    assert panel.get_settings()["house_system"] == "placidus"
