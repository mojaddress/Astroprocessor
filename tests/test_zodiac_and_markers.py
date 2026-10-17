"""Итерация 26: календарь знаков, R-метки, имена знаков на кольце."""
import os
import sys
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import (
    QApplication, QGraphicsPathItem, QGraphicsSimpleTextItem,
)

from astro_core.zodiac_calendar import sign_periods
from ui_qt.widgets.chart_view import ChartView


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication(sys.argv)


def test_sign_periods_cover_year():
    segs = sign_periods(2026)
    assert 12 <= len(segs) <= 14
    assert segs[0][0] == "Capricorn"
    assert segs[0][1] == date(2026, 1, 1)
    assert segs[-1][2] == date(2026, 12, 31)
    for (_s, st, en), (_s2, st2, _e2) in zip(segs, segs[1:]):
        assert st <= en
        assert st2 == en.replace(day=en.day) or st2 > en


def test_retro_marker_present(app):
    data = {
        "birth": {"name": "Т"},
        "planets": [
            {"name": "Mars", "longitude": 100.0, "sign": "Libra", "retrograde": True},
            {"name": "Sun", "longitude": 200.0, "sign": "Libra", "retrograde": False},
        ],
        "houses": [], "aspects": [], "additional_points": [],
    }
    view = ChartView()
    view.set_chart_data(data)
    texts = [i.text() for i in view._scene.items()
             if isinstance(i, QGraphicsSimpleTextItem)]
    assert "R" in texts


def test_sign_names_on_ring(app):
    data = {
        "birth": {"name": "Т"},
        "planets": [{"name": "Sun", "longitude": 45.0, "sign": "Taurus", "retrograde": False}],
        "houses": [], "aspects": [], "additional_points": [],
    }
    view = ChartView()
    view.set_chart_data(data, {"show_sign_names": True})
    texts = [i.text() for i in view._scene.items()
             if isinstance(i, QGraphicsSimpleTextItem)]
    assert "Овен" in texts and "Телец" in texts
