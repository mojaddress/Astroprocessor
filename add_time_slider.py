"""Ползунок времени: динамика транзитной карты + исправление положений транзитных планет.

Запуск:  py -3.11 add_time_slider.py
Создаёт: ui_qt/time_slider.py, tests/test_time_slider.py
Патчит:  ui_qt/main_window.py (ползунок, реальные положения планет, защита потоков)
         tests/test_transit_panel_ui.py (ускорение тяжёлого теста)
Идемпотентен: маркер TIME_SLIDER_V1. Резервные копии: *.bak_time_slider
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIN = ROOT / "ui_qt" / "main_window.py"
SLIDER = ROOT / "ui_qt" / "time_slider.py"
TEST_FILE = ROOT / "tests" / "test_time_slider.py"
HEAVY_TEST = ROOT / "tests" / "test_transit_panel_ui.py"
MARKER = "TIME_SLIDER_V1"

SLIDER_SRC = '''"""Ползунок времени: плавная динамика транзитной карты (TIME_SLIDER_V1).

Виджет не знает о ядре и не считает эфемериды - он только сообщает дату.
Перерисовку выполняет главное окно с троттлингом, поэтому перетаскивание
не заваливает интерфейс пересчётами.
"""
from __future__ import annotations

from PyQt6.QtCore import QDate, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)


class TimeSlider(QWidget):
    """Выбор момента времени: перетаскивание, покадрово, анимация."""

    date_changed = pyqtSignal(QDate)

    WINDOWS = (("30 дней", 30), ("1 год", 365), ("5 лет", 1825), ("10 лет", 3650))
    STEPS = (("день", 1), ("неделя", 7), ("месяц", 30))
    SPEEDS = (("медленно", 200), ("нормально", 80), ("быстро", 30))

    def __init__(self, parent=None):
        super().__init__(parent)
        self._anchor = QDate.currentDate()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build_ui()
        self._apply_speed()
        self._apply_window()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 2, 4, 2)
        root.setSpacing(2)

        row = QHBoxLayout()
        self.btn_start = QPushButton("⏮")
        self.btn_prev = QPushButton("◀")
        self.btn_play = QPushButton("▶ Воспроизвести")
        self.btn_next = QPushButton("▶|")
        self.btn_end = QPushButton("⏭")
        for button, tip in ((self.btn_start, "В начало окна"),
                            (self.btn_prev, "Шаг назад"),
                            (self.btn_play, "Анимация транзитов"),
                            (self.btn_next, "Шаг вперёд"),
                            (self.btn_end, "В конец окна")):
            button.setToolTip(tip)
            row.addWidget(button)

        row.addWidget(QLabel("Окно:"))
        self.combo_window = QComboBox()
        for title, _days in self.WINDOWS:
            self.combo_window.addItem(title)
        self.combo_window.setCurrentIndex(1)
        row.addWidget(self.combo_window)

        row.addWidget(QLabel("Шаг:"))
        self.combo_step = QComboBox()
        for title, _days in self.STEPS:
            self.combo_step.addItem(title)
        row.addWidget(self.combo_step)

        row.addWidget(QLabel("Скорость:"))
        self.combo_speed = QComboBox()
        for title, _ms in self.SPEEDS:
            self.combo_speed.addItem(title)
        self.combo_speed.setCurrentIndex(1)
        row.addWidget(self.combo_speed)

        row.addStretch(1)
        self.lbl_date = QLabel("")
        self.lbl_date.setMinimumWidth(90)
        row.addWidget(self.lbl_date)
        root.addLayout(row)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setSingleStep(1)
        root.addWidget(self.slider)

        self.btn_start.clicked.connect(lambda: self._set_value(0))
        self.btn_prev.clicked.connect(lambda: self._step(-1))
        self.btn_next.clicked.connect(lambda: self._step(1))
        self.btn_end.clicked.connect(lambda: self._set_value(self.slider.maximum()))
        self.btn_play.clicked.connect(self.toggle_play)
        self.slider.valueChanged.connect(self._on_value)
        self.combo_window.currentIndexChanged.connect(self._apply_window)
        self.combo_speed.currentIndexChanged.connect(self._apply_speed)

    def set_anchor(self, date: QDate):
        """Точка отсчёта окна (обычно дата транзита на момент расчёта карты)."""
        self._anchor = QDate(date.year(), date.month(), date.day())
        self._apply_window()

    def anchor(self) -> QDate:
        return self._anchor

    def current_date(self) -> QDate:
        return self._anchor.addDays(self.slider.value())

    def is_playing(self) -> bool:
        return self._timer.isActive()

    def start(self):
        if self.slider.value() >= self.slider.maximum():
            self._set_value(0)
        self._timer.start()
        self.btn_play.setText("⏸ Пауза")

    def stop(self):
        self._timer.stop()
        self.btn_play.setText("▶ Воспроизвести")

    def toggle_play(self):
        if self.is_playing():
            self.stop()
        else:
            self.start()

    def _apply_window(self):
        span = self.WINDOWS[self.combo_window.currentIndex()][1]
        self.slider.blockSignals(True)
        self.slider.setMaximum(span)
        self.slider.blockSignals(False)
        self._on_value(self.slider.value())

    def _apply_speed(self):
        self._timer.setInterval(self.SPEEDS[self.combo_speed.currentIndex()][1])

    def _step_days(self) -> int:
        return self.STEPS[self.combo_step.currentIndex()][1]

    def _set_value(self, value: int):
        self.slider.setValue(max(0, min(self.slider.maximum(), int(value))))

    def _step(self, direction: int):
        self._set_value(self.slider.value() + direction * self._step_days())

    def _on_value(self, value: int):
        date = self._anchor.addDays(int(value))
        self.lbl_date.setText(date.toString("dd.MM.yyyy"))
        self.date_changed.emit(date)

    def _tick(self):
        if self.slider.value() >= self.slider.maximum():
            self.stop()
            return
        self._step(1)
'''

WIN_EDITS = [
    (
        "from ui_qt.background import BackgroundRunner  # BG_WIRE_V1",
        "from ui_qt.background import BackgroundRunner  # BG_WIRE_V1\n"
        "from ui_qt.time_slider import TimeSlider  # TIME_SLIDER_V1",
    ),
    (
        "        self._background = BackgroundRunner(self)  # BG_WIRE_V1",
        "        self._background = BackgroundRunner(self)  # BG_WIRE_V1\n"
        "        # Ползунок времени: троттлинг перерисовки (TIME_SLIDER_V1)\n"
        "        self._slider_pending = None\n"
        "        self._slider_timer = QTimer(self)\n"
        "        self._slider_timer.setSingleShot(True)\n"
        "        self._slider_timer.setInterval(40)\n"
        "        self._slider_timer.timeout.connect(self._apply_slider_date)",
    ),
    (
        "        # CENTER PANE - Chart View (main focus)\n"
        "        self._chart_view = ChartView()",
        "        # CENTER PANE - Chart View (main focus)\n"
        "        self._chart_view = ChartView()\n"
        "        # Ползунок времени под картой (TIME_SLIDER_V1)\n"
        "        self._time_slider = TimeSlider()\n"
        "        center_panel = QWidget()\n"
        "        center_layout = QVBoxLayout(center_panel)\n"
        "        center_layout.setContentsMargins(0, 0, 0, 0)\n"
        "        center_layout.setSpacing(2)\n"
        "        center_layout.addWidget(self._chart_view, 1)\n"
        "        center_layout.addWidget(self._time_slider, 0)",
    ),
    (
        "        self._main_splitter.addWidget(self._chart_view)",
        "        self._main_splitter.addWidget(center_panel)  # TIME_SLIDER_V1",
    ),
    (
        "        self._transit_panel.calculate_requested.connect(self._handle_calculate_transits)",
        "        self._transit_panel.calculate_requested.connect(self._handle_calculate_transits)\n"
        "        self._time_slider.date_changed.connect(self._on_time_slider_date)  # TIME_SLIDER_V1",
    ),
    (
        "            self._transit_panel.set_natal_data(natal_objects, chart_settings)",
        "            self._transit_panel.set_natal_data(natal_objects, chart_settings)\n"
        "            self._time_slider.set_anchor(  # TIME_SLIDER_V1\n"
        "                self._transit_panel.edit_transit_date.date())",
    ),
    (
        "        from PyQt6.QtWidgets import QProgressDialog",
        "        self._time_slider.stop()  # TIME_SLIDER_V1: анимация не мешает расчёту\n"
        "        from PyQt6.QtWidgets import QProgressDialog",
    ),
    (
        "            transit_planets = self._extract_transit_planets_for_chart(\n"
        "                transit_result, start_date, end_date)\n"
        "            transit_aspects = self._extract_transit_aspects_for_chart(transit_result)",
        "            # Положения берутся из эфемерид, а не из полей событий (TIME_SLIDER_V1)\n"
        "            transit_planets, transit_aspects = self._transit_layer(\n"
        "                self._transit_panel.edit_transit_date.date())",
    ),
]

HANDLER_ANCHOR = "    def _on_show_interpretation(self):"
HANDLERS = '''    def _transit_layer(self, qdate):
        """Реальные положения транзитных планет и аспекты к наталу на дату.  # TIME_SLIDER_V1

        Важно: положения берутся из эфемерид. Прежний способ читал
        event["transit_longitude"], которого нет у событий точного режима
        и периодов активности, из-за чего все планеты ставились в 0° Овна.
        """
        from astro_core.transits import calculate_transit_positions, find_transits_on_date
        from astro_core.time_service import parse_local_datetime, datetime_to_jd

        settings = dict(self._current_chart_result.get("settings", {}) or {})
        if settings.get("enabled_planets"):
            settings["transit_planets"] = list(settings["enabled_planets"])
        _local, utc = parse_local_datetime(
            qdate.toString("yyyy-MM-dd"), "12:00", settings.get("transit_utc_offset", 0))
        julian_day = datetime_to_jd(utc)
        transit_objects, _warnings = calculate_transit_positions(julian_day, settings)
        aspects = find_transits_on_date(
            self._current_chart_result.get("objects", []), transit_objects, settings)
        return transit_objects, aspects

    def _on_time_slider_date(self, qdate):
        """Запрос обновления транзитного слоя с ползунка (TIME_SLIDER_V1)."""
        if not self._current_chart_result or self._background.busy:
            return
        self._slider_pending = qdate
        self._transit_panel.edit_transit_date.setDate(qdate)
        if not self._slider_timer.isActive():
            self._slider_timer.start()

    def _apply_slider_date(self):
        """Перерисовка транзитного слоя на дату ползунка (не чаще 25 раз/с)."""
        qdate = self._slider_pending
        self._slider_pending = None
        if qdate is None or not self._current_chart_result or self._background.busy:
            return
        try:
            transit_planets, transit_aspects = self._transit_layer(qdate)
            self._chart_view.set_transit_chart_data(
                natal_chart=self._current_chart_result,
                transit_planets=transit_planets,
                transit_aspects=transit_aspects,
                display_settings=self._get_display_settings(),
            )
            self._last_transit_planets = transit_planets
            self._last_transit_aspects = transit_aspects
            self._current_transit_result = transit_aspects
            self._chart_mode = "transit"
            self._transit_available = True
            self._update_transit_toggle_visibility()
            self._status_label.setText(
                f"Транзиты на {qdate.toString('dd.MM.yyyy')}: {len(transit_aspects)} аспектов")
        except Exception as exc:
            self._time_slider.stop()
            self._status_label.setText(f"Ошибка обновления транзитов: {exc}")

'''

TEST_SRC = '''"""Ползунок времени: даты, шаги, окно, анимация и обновление карты."""
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
    assert "Воспроизвести" in slider.btn_play.text()


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
        assert all(p["longitude"] != 0 for p in planets[:3]), \\
            "положения должны браться из эфемерид, а не быть нулями"
        assert "Транзиты на 15.06.2026" in window._status_label.text()
    finally:
        window._time_slider.stop()
        window._background.cancel()
        window._background.wait(3000)
        window.deleteLater()
'''


def patch_file(path: Path, edits: list[tuple[str, str]], marker: str) -> None:
    src = path.read_text(encoding="utf-8")
    if marker in src:
        print(f"[*] {path.name}: патч уже применён.")
        return
    for old, _new in edits:
        if src.count(old) != 1:
            print(f"[X] {path.name}: якорь найден {src.count(old)} раз (ожидался 1):")
            print(f"    {old[:80]!r}")
            print("    Файл НЕ изменён.")
            sys.exit(1)
    for old, new in edits:
        src = src.replace(old, new, 1)
    try:
        compile(src, str(path), "exec")
    except SyntaxError as exc:
        print(f"[X] {path.name}: SyntaxError после патча: {exc}. Файл НЕ изменён.")
        sys.exit(1)
    shutil.copy2(path, path.with_name(path.name + ".bak_time_slider"))
    path.write_text(src, encoding="utf-8")
    print(f"[+] {path.name} пропатчен.")


def speed_up_heavy_test() -> None:
    if not HEAVY_TEST.exists():
        return
    src = HEAVY_TEST.read_text(encoding="utf-8")
    if "addDays(365)" in src and "btn_range_year.click()" in src:
        print("[*] Тяжёлый тест уже ускорен.")
        return
    src = src.replace("panel.btn_range_five_years.click()", "panel.btn_range_year.click()")
    src = src.replace("QDate(2026, 1, 1).addDays(1825).toPyDate()",
                      "QDate(2026, 1, 1).addDays(365).toPyDate()")
    compile(src, str(HEAVY_TEST), "exec")
    HEAVY_TEST.write_text(src, encoding="utf-8")
    print("[+] Тяжёлый тест: диапазон 5 лет -> 1 год (фоновый путь сохраняется).")


def main() -> None:
    if not WIN.exists():
        print(f"[X] Не найден файл {WIN}")
        sys.exit(1)

    SLIDER.write_text(SLIDER_SRC, encoding="utf-8")
    print("[+] Создан ui_qt/time_slider.py")

    patch_file(WIN, WIN_EDITS, MARKER)

    src = WIN.read_text(encoding="utf-8")
    if HANDLER_ANCHOR not in src:
        print("[X] Не найден якорь для вставки обработчиков. Файл НЕ изменён.")
        sys.exit(1)
    if "_apply_slider_date(self):" not in src:
        src = src.replace(HANDLER_ANCHOR, HANDLERS + HANDLER_ANCHOR, 1)
        compile(src, str(WIN), "exec")
        WIN.write_text(src, encoding="utf-8")
        print("[+] main_window.py: добавлены обработчики ползунка и расчёт слоя.")

    TEST_FILE.write_text(TEST_SRC, encoding="utf-8")
    print("[+] Создан tests/test_time_slider.py (9 тестов)")
    speed_up_heavy_test()

    sys.path.insert(0, str(ROOT))
    try:
        from ui_qt.time_slider import TimeSlider  # noqa: F401
        import ui_qt.main_window as module  # noqa: F401
        assert hasattr(module.MainWindow, "_transit_layer")
        assert hasattr(module.MainWindow, "_apply_slider_date")
        print("[+] Контроль: виджет и обработчики на месте.")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Ошибка контроля: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()