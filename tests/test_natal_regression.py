"""Регрессия: расчёт натала не переключается на транзитный вид."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QDate, QEventLoop, QTime, QTimer
from PyQt6.QtWidgets import QApplication

from ui_qt.time_slider import TimeSlider


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def slider(qapp):
    widget = TimeSlider()
    widget.set_anchor(QDate(2026, 1, 1))
    yield widget
    widget.stop()
    widget.deleteLater()


def _drain(ms=120):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_set_anchor_does_not_emit(slider):
    seen = []
    slider.date_changed.connect(lambda date: seen.append(date))
    slider.set_anchor(QDate(2027, 3, 5))
    _drain()
    assert seen == [], "программная установка точки отсчёта не должна подавать сигнал"
    assert slider.lbl_date.text() == "05.03.2027"


def test_window_change_does_not_emit(slider):
    seen = []
    slider.date_changed.connect(lambda date: seen.append(date))
    slider.combo_window.setCurrentIndex(2)
    _drain()
    assert seen == []
    assert slider.slider.maximum() == 1825


def test_user_drag_still_emits(slider):
    seen = []
    slider.date_changed.connect(lambda date: seen.append(date))
    slider.slider.setValue(12)
    assert seen and seen[-1] == QDate(2026, 1, 13)


def test_buttons_still_emit(slider):
    seen = []
    slider.date_changed.connect(lambda date: seen.append(date))
    slider.btn_next.click()
    assert seen and seen[-1] == QDate(2026, 1, 2)


def test_natal_view_survives_calculate(qapp):
    from ui_qt.main_window import MainWindow

    window = MainWindow()
    try:
        panel = window._birth_input_panel
        panel.edit_name.setText("Regression")
        panel.edit_birth_date.setDate(QDate(1990, 5, 15))
        panel.edit_birth_time.setTime(QTime(14, 30))
        panel.spin_latitude.setValue(55.7558)
        panel.spin_longitude.setValue(37.6173)
        panel.spin_utc_offset.setValue(3.0)

        window._on_calculate_chart()
        _drain(250)  # даём отработать отложенным таймерам ползунка

        assert window._current_chart_result is not None
        assert window._chart_mode == "natal",             "после расчёта натала вид не должен переключаться на транзиты"
        assert window._slider_pending is None
        assert not window._slider_timer.isActive()
    finally:
        window._time_slider.stop()
        window._background.cancel()
        window._background.wait(3000)
        window.deleteLater()
