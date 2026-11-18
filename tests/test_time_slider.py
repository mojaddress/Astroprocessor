"""Ползунок времени: даты, шаги, окно, анимация и обновление карты."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QApplication

from ui_qt.time_slider import TimeSlider

BIRTH = {
    "name": "SliderTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}


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


def test_initial_date_is_anchor(slider):
    assert slider.slider.value() == 0
    assert slider.lbl_date.text() == "01.01.2026"
    assert slider.current_date() == QDate(2026, 1, 1)


def test_slider_emits_date(slider):
    seen = []
    slider.date_changed.connect(lambda date: seen.append(date))
    slider.slider.setValue(10)
    assert seen[-1] == QDate(2026, 1, 11)
    assert slider.lbl_date.text() == "11.01.2026"


def test_step_forward_and_back(slider):
    slider.combo_step.setCurrentIndex(1)  # неделя
    slider.btn_next.click()
    assert slider.slider.value() == 7
    slider.btn_prev.click()
    assert slider.slider.value() == 0


def test_window_changes_maximum(slider):
    slider.combo_window.setCurrentIndex(2)  # 5 лет
    assert slider.slider.maximum() == 1825


def test_play_pause_toggles(slider):
    slider.btn_play.click()
    assert slider.is_playing()
    assert "Пауза" in slider.btn_play.text()
    slider.btn_play.click()
    assert not slider.is_playing()
    assert "Пуск" in slider.btn_play.text()


def test_tick_advances_and_stops_at_end(slider):
    slider.combo_window.setCurrentIndex(0)  # 30 дней
    slider.combo_step.setCurrentIndex(0)    # день
    slider.slider.setValue(29)
    slider.start()
    slider._tick()
    assert slider.slider.value() == 30
    slider._tick()
    assert not slider.is_playing()


def test_set_anchor_updates_label(slider):
    slider.set_anchor(QDate(2027, 5, 10))
    assert slider.lbl_date.text() == "10.05.2027"


def test_jump_to_end(slider):
    slider.btn_end.click()
    assert slider.slider.value() == slider.slider.maximum()
    slider.btn_start.click()
    assert slider.slider.value() == 0


def test_main_window_slider_updates_transit_layer(qapp):
    """Интеграция: ползунок рисует реальные положения, а не нули."""
    from astro_core.chart import build_natal_chart
    from ui_qt.main_window import MainWindow

    chart = build_natal_chart(BIRTH, {})
    window = MainWindow()
    try:
        window._current_chart_result = chart
        window._current_birth_data = BIRTH
        window._time_slider.set_anchor(QDate(2026, 6, 1))
        window._on_time_slider_date(QDate(2026, 6, 15))
        window._apply_slider_date()

        assert window._chart_mode == "transit"
        planets = window._last_transit_planets
        assert planets, "транзитный слой должен содержать планеты"
        assert all(p["longitude"] != 0 for p in planets[:3]), \
            "положения должны браться из эфемерид, а не быть нулями"
        assert "Транзиты на 15.06.2026" in window._status_label.text()
    finally:
        window._time_slider.stop()
        window._background.cancel()
        window._background.wait(3000)
        window.deleteLater()
