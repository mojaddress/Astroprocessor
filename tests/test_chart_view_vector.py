"""
Регрессионные тесты векторного рендера карты (итерации 16-18).

Проверяют:
- сцена векторная, без растровых элементов;
- глифы есть для всех объектов (натал и транзит);
- заголовки «Натальная карта: …» и «Транзитная карта: …»;
- тултипы объектов содержат данные (имя, градус, дом);
- легенда аспектов отображается и отключается настройкой show_legend;
- экспорт в изображение и зум работают.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import (
    QApplication, QGraphicsPixmapItem, QGraphicsPathItem, QGraphicsSimpleTextItem,
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
        "birth": {"name": "Тест"},
        "planets": [
            {"name": n, "longitude": lon, "sign": "Aries",
             "degree_in_sign": lon % 30.0, "house": (int(lon // 30) % 12) + 1,
             "retrograde": False, "speed_longitude": 0.5}
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


def _texts(view):
    return [i.text() for i in view._scene.items()
            if isinstance(i, QGraphicsSimpleTextItem)]


def test_natal_scene_contains_glyphs_for_all_objects(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
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


def test_natal_title_present(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
    assert any(t.startswith("Натальная карта:") for t in _texts(view))


def test_transit_title_present(app):
    view = ChartView()
    view.set_transit_chart_data(_chart_data(), [
        {"name": "Sun", "longitude": 190, "sign": "Libra", "retrograde": False},
    ], [])
    assert any(t.startswith("Транзитная карта:") for t in _texts(view))


def test_objects_have_tooltips(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
    tips = [i.toolTip() for i in view._scene.items() if i.toolTip()]
    assert len(tips) >= len(PLANETS)
    assert any("Солнце" in t for t in tips)
    assert any("°" in t for t in tips)


def test_legend_present_and_toggle(app):
    view = ChartView()
    view.set_chart_data(_chart_data())
    assert "Соединение" in _texts(view)
    assert "Оппозиция" in _texts(view)

    view2 = ChartView()
    view2.set_chart_data(_chart_data(), {"show_legend": False})
    assert "Соединение" not in _texts(view2)