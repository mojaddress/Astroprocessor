"""
Регрессионные тесты векторного рендера карты (дефекты I-1, I-2, итерация 16).

Проверяют:
- сцена строится и содержит векторные глифы для всех планет;
- в сцене НЕТ растровых элементов (QGraphicsPixmapItem);
- транзитная карта содержит глифы обоих колец;
- экспорт в изображение работает.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import (
    QApplication, QGraphicsPixmapItem, QGraphicsPathItem,
)

from ui_qt.widgets.chart_view import ChartView

PLANETS = [
    ("Sun", 45), ("Moon", 120), ("Mercury", 52), ("Venus", 80),
    ("Mars", 200), ("Jupiter", 250), ("Saturn", 300),
    ("MeanNode", 150), ("Chiron", 20),
]


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication(sys.argv)


def _chart_data():
    return {
        "planets": [
            {"name": n, "longitude": lon, "sign": "Aries", "retrograde": False}
            for n, lon in PLANETS
        ],
        "houses": [{"house": i + 1, "longitude": i * 30} for i in range(12)],
        "aspects": [{"point_a": "Sun", "point_b": "Mars", "aspect": "opposition"}],
        "additional_points": [
            {"name": "ASC", "longitude": 0},
            {"name": "MC", "longitude": 270},
        ],
    }


def _glyph_items(view):
    return [i for i in view._scene.items() if isinstance(i, QGraphicsPathItem)]


def test_natal_scene_contains_glyphs_for_all_objects(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
    # по одному глиф-пути на каждый объект (Sun, Moon, ..., Node, Chiron)
    assert len(_glyph_items(view)) >= len(PLANETS)


def test_scene_is_pure_vector_no_pixmaps(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
    rasters = [i for i in view._scene.items() if isinstance(i, QGraphicsPixmapItem)]
    assert rasters == [], "Сцена должна быть векторной без QPixmap"


def test_transit_scene_contains_both_rings_glyphs(app):
    view = ChartView()
    transit = [
        {"name": "Sun", "longitude": 190, "sign": "Libra", "retrograde": False},
        {"name": "Moon", "longitude": 10, "sign": "Aries", "retrograde": False},
        {"name": "MeanNode", "longitude": 300, "sign": "Aquarius", "retrograde": False},
    ]
    aspects = [{"transit_planet": "Sun", "natal_point": "Venus", "aspect": "trine"}]
    view.set_transit_chart_data(_chart_data(), transit, aspects)
    assert len(_glyph_items(view)) >= len(PLANETS) + len(transit)


def test_render_to_image_export(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
    image = view.render_to_image(600, 600)
    assert not image.isNull()
    assert image.width() == 600


def test_zoom_and_reset_do_not_crash(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
    view.zoom_in()
    view.zoom_out()
    view.reset_view()
    assert view.get_zoom() == pytest.approx(1.0)