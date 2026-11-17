"""UX панели транзитов: кнопка расчёта, пресеты диапазона, понятная таблица периодов.

Запуск:  py -3.11 improve_transit_ui.py
Патчит:  ui_qt/widgets/transit_panel.py
Создаёт: tests/test_transit_panel_ui.py
Идемпотентен: маркер TRANSIT_UX_V1. Резервная копия: transit_panel.py.bak_transit_ux
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "ui_qt" / "widgets" / "transit_panel.py"
TEST_FILE = ROOT / "tests" / "test_transit_panel_ui.py"
MARKER = "TRANSIT_UX_V1"

BUTTON_ANCHOR = "        # --- Calculate Button ---"
BUTTON_BLOCK = '''        # --- Calculate Button --- TRANSIT_UX_V1
        self.btn_calculate = QPushButton("🔄 Рассчитать транзиты")
        self.btn_calculate.setToolTip("Пересчитать с текущими настройками (F6)")
        self.btn_calculate.clicked.connect(self._on_calculate)
        layout.addWidget(self.btn_calculate)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Диапазон:"))
        self.btn_range_month = QPushButton("1 мес")
        self.btn_range_year = QPushButton("1 год")
        self.btn_range_five_years = QPushButton("5 лет")
        for button, days in ((self.btn_range_month, 30),
                             (self.btn_range_year, 365),
                             (self.btn_range_five_years, 1825)):
            button.setToolTip("Задать диапазон от даты транзита, затем нажать «Рассчитать»")
            button.clicked.connect(lambda _=False, span=days: self._apply_range_preset(span))
            preset_row.addWidget(button)
        layout.addLayout(preset_row)
'''

RESULTS_ANCHOR = "    @pyqtSlot(list)\n    def set_results(self, results: List[Dict]):"

RESULTS_BLOCK = '''    def _apply_range_preset(self, days: int):
        """Задаёт диапазон от даты транзита и включает режим диапазона (TRANSIT_UX_V1)."""
        start = self.edit_transit_date.date()
        self.radio_date_range.setChecked(True)
        self.edit_start_date.setDate(start)
        self.edit_end_date.setDate(start.addDays(days))

    @pyqtSlot(list)
    def set_results(self, results: List[Dict]):
        """Показывает результат понятными колонками (TRANSIT_UX_V1).

        Режим определяется по составу записи: периоды активности, точные
        транзиты или календарь по дням. Технические поля (jd, target_longitude)
        не показываются - они не нужны пользователю.
        """
        from astro_core.constants import (
            ASPECT_NAMES_RU, DIRECTION_NAMES_RU, PLANET_NAMES_RU,
        )

        self.table_results.setRowCount(0)
        if not results:
            self.table_results.setColumnCount(0)
            return

        sample = results[0]
        if "start_datetime" in sample:
            schema = [
                ("transit_planet", "Планета"),
                ("natal_point", "Натальная точка"),
                ("aspect", "Аспект"),
                ("start_datetime", "Вход в орб"),
                ("exact_datetime", "Пик"),
                ("end_datetime", "Выход из орба"),
                ("_duration", "Длительность, дн"),
                ("direction", "Направление"),
                ("orb", "Орб, °"),
            ]
        elif "exact_datetime" in sample:
            schema = [
                ("exact_datetime", "Точное время"),
                ("transit_planet", "Планета"),
                ("natal_point", "Натальная точка"),
                ("aspect", "Аспект"),
                ("direction", "Направление"),
            ]
        elif "date" in sample:
            schema = [
                ("date", "Дата"),
                ("transit_planet", "Планета"),
                ("natal_point", "Натальная точка"),
                ("aspect", "Аспект"),
                ("orb", "Орб, °"),
                ("strength", "Сила"),
            ]
        else:
            schema = [(key, key) for key in sample.keys()]

        self.table_results.setColumnCount(len(schema))
        self.table_results.setHorizontalHeaderLabels([title for _, title in schema])
        self.table_results.setRowCount(len(results))

        for row, record in enumerate(results):
            for column, (key, _title) in enumerate(schema):
                text = self._format_cell(key, record, ASPECT_NAMES_RU,
                                         DIRECTION_NAMES_RU, PLANET_NAMES_RU)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_results.setItem(row, column, item)

        self.table_results.resizeColumnsToContents()

    @staticmethod
    def _format_cell(key, record, aspect_ru, direction_ru, planet_ru):
        """Значение ячейки в виде, понятном астрологу, а не программе."""
        if key == "_duration":
            start = record.get("start_jd")
            end = record.get("end_jd")
            if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                return f"{end - start:.1f}"
            return ""

        value = record.get(key, "")
        if key in ("transit_planet", "natal_point"):
            return planet_ru.get(value, str(value))
        if key == "aspect":
            return aspect_ru.get(value, str(value))
        if key == "direction":
            return direction_ru.get(value, str(value))
        if key in ("start_datetime", "exact_datetime", "end_datetime"):
            text = str(value)
            if "T" in text:
                date_part, time_part = text.split("T", 1)
                pieces = date_part.split("-")
                if len(pieces) == 3:
                    year, month, day = pieces
                    return f"{day}.{month}.{year} {time_part[:5]}"
            return text
        if key == "date":
            pieces = str(value).split("-")
            if len(pieces) == 3:
                year, month, day = pieces
                return f"{day}.{month}.{year}"
            return str(value)
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)
'''

TEST_SRC = '''"""UX панели транзитов: кнопка, пресеты диапазона, понятная таблица периодов."""
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
'''


def main() -> None:
    if not TARGET.exists():
        print(f"[X] Не найден файл {TARGET}")
        sys.exit(1)

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print("[*] UX-патч уже применён.")
    else:
        if src.count(BUTTON_ANCHOR) != 1 or src.count(RESULTS_ANCHOR) != 1:
            print("[X] Якоря не найдены однозначно. Файл НЕ изменён.")
            sys.exit(1)
        head = src[:src.index(RESULTS_ANCHOR)]
        src = head + RESULTS_BLOCK
        src = src.replace(BUTTON_ANCHOR, BUTTON_BLOCK, 1)
        try:
            compile(src, str(TARGET), "exec")
        except SyntaxError as exc:
            print(f"[X] SyntaxError после патча: {exc}. Файл НЕ изменён.")
            sys.exit(1)
        shutil.copy2(TARGET, TARGET.with_name(TARGET.name + ".bak_transit_ux"))
        TARGET.write_text(src, encoding="utf-8")
        print("[+] transit_panel.py: кнопка расчёта, пресеты диапазона, понятная таблица.")

    TEST_FILE.write_text(TEST_SRC, encoding="utf-8")
    print("[+] Создан tests/test_transit_panel_ui.py (7 тестов)")

    sys.path.insert(0, str(ROOT))
    try:
        from ui_qt.widgets import transit_panel as module  # noqa: F401
        assert hasattr(module.TransitPanel, "_apply_range_preset")
        assert hasattr(module.TransitPanel, "_format_cell")
        print("[+] Контроль: новые методы панели на месте.")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Ошибка контроля: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()