"""Тесты провайдера цветов полотна карты (ui_qt.chart_theme)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtGui import QColor

from ui_qt import chart_theme


@pytest.fixture(autouse=True)
def reset_state():
    chart_theme.set_dark(False)
    yield
    chart_theme.set_dark(False)


def test_light_background_and_ink():
    assert chart_theme.bg().name() == "#ffffff"
    assert chart_theme.ink_hex() == "#000000"


def test_dark_background_and_ink():
    chart_theme.set_dark(True)
    assert chart_theme.bg().name() == "#17181a"
    assert chart_theme.ink_hex() == "#E8EAED"


def test_adapt_noop_on_light():
    c = QColor("#000000")
    assert chart_theme.adapt(c).name() == "#000000"


def test_adapt_lightens_dark_ink_on_dark():
    chart_theme.set_dark(True)
    assert chart_theme.adapt(QColor("#000000")).getHsvF()[2] >= 0.55
    assert chart_theme.adapt(QColor("#666666")).getHsvF()[2] >= 0.55


def test_adapt_keeps_bright_colors():
    chart_theme.set_dark(True)
    bright = QColor("#FFD700")
    assert chart_theme.adapt(bright).name() == bright.name()


def test_adapt_preserves_transparency():
    chart_theme.set_dark(True)
    transparent = QColor(0, 0, 0, 0)
    assert chart_theme.adapt(transparent).alpha() == 0


def test_adapt_idempotent():
    chart_theme.set_dark(True)
    once = chart_theme.adapt(QColor("#101010"))
    twice = chart_theme.adapt(once)
    assert once.name() == twice.name()


def test_rendered_flag():
    assert chart_theme.was_rendered() in (True, False)
    chart_theme.mark_rendered()
    assert chart_theme.was_rendered() is True
