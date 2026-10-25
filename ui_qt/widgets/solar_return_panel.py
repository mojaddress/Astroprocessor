"""
Панель «☀️ Обращения» (солнечные возвращения) — итерация 30.
"""
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox,
    QRadioButton, QComboBox, QTableWidget, QTableWidgetItem,
    QTextBrowser, QGroupBox, QHeaderView,
)
from PyQt6.QtCore import pyqtSignal

from astro_core.constants import get_planet_name_ru, get_sign_name_ru
from astro_core.interpretations import DISCLAIMER
from astro_core.solar_return import calculate_solar_return, summarize_solar_return

from .birth_input_panel import CityCompleter


class SolarReturnPanel(QWidget):
    """Соляр: год, город, таблица планет, трактовка, вывод карты."""

    chart_ready = pyqtSignal(object, int)
    help_requested = pyqtSignal(str)

    def __init__(self, get_chart, city_controller, parent=None):
        super().__init__(parent)
        self._get_chart = get_chart
        self._city_controller = city_controller
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        group = QGroupBox("☀️ Солнечное обращение (соляр)")
        gl = QVBoxLayout(group)
        row = QHBoxLayout()
        row.addWidget(QLabel("Год:"))
        self.spin_year = QSpinBox()
        self.spin_year.setRange(1900, 2100)
        self.spin_year.setValue(date.today().year)
        row.addWidget(self.spin_year)
        row.addStretch(1)
        self.btn_calculate = QPushButton("☀️ Рассчитать")
        self.btn_calculate.clicked.connect(self._on_calculate)
        row.addWidget(self.btn_calculate)
        self.btn_help = QPushButton("📖")
        self.btn_help.setToolTip("База Знаний: Обращения")
        self.btn_help.clicked.connect(lambda _=False: self.help_requested.emit("id:solar-return"))
        row.addWidget(self.btn_help)
        gl.addLayout(row)
        city_row = QHBoxLayout()
        self.radio_birth = QRadioButton("Координаты рождения")
        self.radio_birth.setChecked(True)
        self.radio_city = QRadioButton("Выбрать город")
        city_row.addWidget(self.radio_birth)
        city_row.addWidget(self.radio_city)
        gl.addLayout(city_row)
        self._city_completer = CityCompleter(self._city_controller, self)
        self.combo_city = QComboBox()
        self.combo_city.setEditable(True)
        self.combo_city.setCompleter(self._city_completer)
        self.combo_city.lineEdit().textChanged.connect(self._on_city_query)
        self._city_completer.activated.connect(self._on_city_activated)
        gl.addWidget(self.combo_city)
        layout.addWidget(group)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Планета", "Долгота", "Знак", "Дом", "Ретро"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)
        self.text_summary = QTextBrowser()
        self.text_summary.setOpenExternalLinks(False)
        layout.addWidget(self.text_summary, 1)
        self._populate_cities()

    def _populate_cities(self):
        cities = self._city_controller.get_all_cities()[:20]
        self.combo_city.blockSignals(True)
        self.combo_city.clear()
        for c in cities:
            self.combo_city.addItem(self._city_controller.get_city_display_name(c))
        self.combo_city.blockSignals(False)

    def _on_city_query(self, text: str):
        self._city_completer._update_model(text)

    def _on_city_activated(self, text: str):
        idx = self.combo_city.findText(text)
        if idx < 0:
            self.combo_city.insertItem(0, text)
            idx = 0
        self.combo_city.setCurrentIndex(idx)

    def _on_calculate(self):
        chart = self._get_chart()
        if not chart:
            self.text_summary.setPlainText(
                "Нет натальной карты.\nСначала рассчитайте натальную карту.")
            return
        year = self.spin_year.value()
        if self.radio_city.isChecked():
            city = self._city_controller.get_city_by_name(
                self.combo_city.currentText())
            if city is None:
                self.text_summary.setPlainText(
                    "Город не найден в базе.\nВыберите город из подсказок "
                    "или переключитесь на «Координаты рождения».")
                return
            lat, lon = city.latitude, city.longitude
        else:
            lat = chart["birth"]["latitude"]
            lon = chart["birth"]["longitude"]
        try:
            sr = calculate_solar_return(chart, year, lat, lon)
        except Exception as e:
            self.text_summary.setPlainText(
                f"Не удалось рассчитать соляр:\n{e}")
            return
        self._fill_table(sr["chart"])
        self.text_summary.setPlainText(
            summarize_solar_return(sr["chart"], year, sr["moment_utc"])
            + "\n\n" + DISCLAIMER)
        self.chart_ready.emit(sr["chart"], year)

    def _fill_table(self, chart):
        planets = chart.get("planets", [])
        self.table.setRowCount(len(planets))
        for r, p in enumerate(planets):
            lon = p.get("longitude") or 0.0
            values = [
                get_planet_name_ru(p["name"]),
                f"{lon:.2f}",
                get_sign_name_ru(p.get("sign", "")),
                str(p.get("house") or "—"),
                "R" if p.get("retrograde") else "",
            ]
            for c, v in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(v))
