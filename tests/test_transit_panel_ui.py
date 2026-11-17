"""UX панели транзитов: кнопка, пресеты диапазона, понятная таблица периодов."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QDate, QTimer
from PyQt6.QtWidgets import QApplication

from astro_core.chart import build_natal_chart
from astro_core.controllers import CityController, TransitController
from ui_qt.widgets.transit_panel import TransitPanel

BIRTH = {
    "name": "UiTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="module")
def chart():
    return build_natal_chart(BIRTH, {})


@pytest.fixture
def panel(qapp):
    widget = TransitPanel(TransitController(), CityController())
    yield widget
    widget.deleteLater()


def _headers(panel):
    return [panel.table_results.horizontalHeaderItem(i).text()
            for i in range(panel.table_results.columnCount())]


def test_calculate_button_exists(panel):
    assert panel.btn_calculate is not None
    assert "Рассчитать" in panel.btn_calculate.text()


def test_year_preset_sets_range_and_enables_fields(panel):
    panel.edit_transit_date.setDate(QDate(2026, 1, 1))
    panel.btn_range_year.click()
    assert panel.radio_date_range.isChecked()
    assert panel.edit_start_date.isEnabled()
    assert panel.edit_start_date.date() == QDate(2026, 1, 1)
    assert panel.edit_end_date.date() == QDate(2026, 1, 1).addDays(365)


def test_five_year_preset(panel):
    panel.edit_transit_date.setDate(QDate(2026, 1, 1))
    panel.btn_range_five_years.click()
    assert panel.edit_start_date.date().daysTo(panel.edit_end_date.date()) == 1825


def test_periods_table_is_human_readable(panel, chart):
    controller = TransitController()
    periods = controller.calculate_transits(
        chart["objects"], "2026-01-01", "2026-01-10",
        controller.get_default_settings(), mode="periods")
    assert periods
    panel.set_results(periods)
    headers = _headers(panel)
    for expected in ("Вход в орб", "Пик", "Выход из орба", "Длительность, дн"):
        assert expected in headers
    for technical in ("start_jd", "exact_jd", "end_jd", "target_longitude"):
        assert technical not in headers
    assert panel.table_results.rowCount() == len(periods)


def test_duration_cell_is_positive_number(panel, chart):
    controller = TransitController()
    periods = controller.calculate_transits(
        chart["objects"], "2026-01-01", "2026-01-10",
        controller.get_default_settings(), mode="periods")
    panel.set_results(periods)
    column = _headers(panel).index("Длительность, дн")
    value = float(panel.table_results.item(0, column).text())
    assert value > 0


def test_datetime_cell_is_formatted(panel, chart):
    controller = TransitController()
    periods = controller.calculate_transits(
        chart["objects"], "2026-01-01", "2026-01-05",
        controller.get_default_settings(), mode="periods")
    panel.set_results(periods)
    column = _headers(panel).index("Пик")
    text = panel.table_results.item(0, column).text()
    assert "T" not in text and "." in text and ":" in text


def test_background_dialog_appears_for_long_range(qapp, chart):
    """Интеграция: реальное главное окно, режим периодов, 5 лет."""
    from ui_qt.main_window import MainWindow

    window = MainWindow()
    try:
        window._current_chart_result = chart
        window._current_birth_data = BIRTH
        panel = window._transit_panel
        panel.set_natal_data(chart["objects"], chart.get("settings", {}))
        panel.radio_periods.setChecked(True)
        panel.edit_transit_date.setDate(QDate(2026, 1, 1))
        panel.btn_range_five_years.click()

        QTimer.singleShot(600, lambda: _hide_dialogs(window))
        window._handle_calculate_transits(
            "periods", QDate(2026, 1, 1).toPyDate(),
            QDate(2026, 1, 1).addDays(1825).toPyDate(), [], [])

        assert window._background.busy, "длинный расчёт должен уйти в фон"

        deadline = QTimer()
        deadline.setSingleShot(True)
        from PyQt6.QtCore import QEventLoop
        loop = QEventLoop()
        deadline.timeout.connect(loop.quit)
        deadline.start(20000)
        while window._background.busy and deadline.isActive():
            QApplication.processEvents()
            _hide_dialogs(window)
        loop.quit()

        assert not window._background.busy
        assert panel.table_results.rowCount() > 0
    finally:
        window._background.cancel()
        window._background.wait(5000)
        window.deleteLater()


def _hide_dialogs(window):
    from PyQt6.QtWidgets import QProgressDialog
    for dialog in window.findChildren(QProgressDialog):
        dialog.hide()
