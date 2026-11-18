"""Ползунок времени: одна строка управления, элементы видимы."""
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


def test_slider_has_single_control_row(window):
    assert window._time_slider.layout().count() == 2,         "ожидается одна строка управления + строка ползунка"


def test_slider_controls_visible(window):
    slider = window._time_slider
    for button in (slider.btn_start, slider.btn_prev, slider.btn_play,
                   slider.btn_next, slider.btn_end):
        assert button.width() >= 20
    for combo in (slider.combo_window, slider.combo_step, slider.combo_speed):
        assert combo.width() >= 40


def test_slider_fits_center_pane(window):
    need = window._time_slider.minimumSizeHint().width()
    have = window._main_splitter.widget(1).width()
    assert need <= have, f"ползунку нужно {need}px, центру дано {have}px"


def test_center_minimum_accommodates_slider(window):
    assert window._main_splitter.widget(1).minimumWidth() >= 440
