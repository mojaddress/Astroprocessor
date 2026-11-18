"""Компактная компоновка: двухколоночные сетки и видимые элементы ползунка."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _drain(ms=200):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


@pytest.fixture
def window(qapp):
    from ui_qt.main_window import MainWindow
    win = MainWindow()
    win.resize(1400, 900)
    win.show()
    _drain(250)
    yield win
    win._time_slider.stop()
    win._background.cancel()
    win._background.wait(3000)
    win.deleteLater()


def test_object_grid_two_columns(window):
    grid = window._birth_input_panel.chk_asteroids.parentWidget().layout()
    assert grid.columnCount() <= 2


def test_label_grid_two_columns(window):
    grid = window._birth_input_panel.chk_start_dsc.parentWidget().layout()
    assert grid.columnCount() <= 2


def test_all_object_boxes_placed(window):
    panel = window._birth_input_panel
    grid = panel.chk_asteroids.parentWidget().layout()
    placed = {grid.itemAt(i).widget() for i in range(grid.count())}
    for name in ("chk_chiron", "chk_nodes", "chk_fortune", "chk_cross",
                 "chk_blackmoon", "chk_selena", "chk_proserpina",
                 "chk_asteroids", "chk_vertex"):
        assert getattr(panel, name) in placed


def test_city_buttons_short_text(window):
    panel = window._birth_input_panel
    assert panel.btn_save_profile.text() == "💾 В профиль"
    assert "Координаты" in panel.manual_coords_header.text()


def test_slider_buttons_visible(window):
    slider = window._time_slider
    for button in (slider.btn_start, slider.btn_prev, slider.btn_play,
                   slider.btn_next, slider.btn_end):
        assert button.width() >= 20, f"кнопка {button.toolTip()} схлопнута"


def test_slider_combos_visible(window):
    slider = window._time_slider
    for combo in (slider.combo_window, slider.combo_step, slider.combo_speed):
        assert combo.width() >= 40, "комбо ползунка схлопнуто"


def test_slider_fits_center_pane(window):
    need = window._time_slider.minimumSizeHint().width()
    have = window._main_splitter.widget(1).width()
    assert need <= have, f"ползунку нужно {need}px, центру дано {have}px"
