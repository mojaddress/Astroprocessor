"""
Панель «Дирекции» — солнечная дуга (итерация 27).
"""
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTextBrowser, QGroupBox, QHeaderView,
)
from PyQt6.QtCore import QDate, pyqtSignal

from astro_core.constants import get_planet_name_ru, get_sign_name_ru
from astro_core.interpretations import ASPECT_INFO, DISCLAIMER


class DirectionsPanel(QWidget):
    """Дирекции солнечной дуги: дата, дуга, таблицы, сводка."""

    calculate_requested = pyqtSignal(object)
    help_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_text = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        group = QGroupBox("🌀 Дирекции (солнечная дуга)")
        gl = QHBoxLayout(group)
        gl.addWidget(QLabel("Дата:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        gl.addWidget(self.date_edit)
        self.btn_calculate = QPushButton("🌀 Рассчитать")
        self.btn_calculate.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_calculate.clicked.connect(self._on_calculate)
        gl.addWidget(self.btn_calculate)
        self.btn_help = QPushButton("📖")
        self.btn_help.setToolTip("База Знаний: Дирекции")
        self.btn_help.clicked.connect(lambda _=False: self.help_requested.emit("Дирекции"))
        gl.addWidget(self.btn_help)
        layout.addWidget(group)

        self.lbl_arc = QLabel("Солнечная дуга: —")
        self.lbl_arc.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_arc)

        self.table_planets = QTableWidget(0, 4)
        self.table_planets.setHorizontalHeaderLabels(
            ["Дир. планета", "Долгота", "Знак", "° в знаке"])
        self.table_planets.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table_planets.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_planets, 2)

        self.table_aspects = QTableWidget(0, 5)
        self.table_aspects.setHorizontalHeaderLabels(
            ["Дир. планета", "Натальная точка", "Аспект", "Орб", "Баллы"])
        self.table_aspects.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table_aspects.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_aspects, 3)

        self.text_summary = QTextBrowser()
        layout.addWidget(self.text_summary, 2)

    def _on_calculate(self):
        qd = self.date_edit.date()
        self.calculate_requested.emit(date(qd.year(), qd.month(), qd.day()))

    def set_results(self, result):
        arc = result["arc"]
        deg = int(arc)
        mins = int(round((arc - deg) * 60))
        if mins == 60:
            deg, mins = deg + 1, 0
        self.lbl_arc.setText(f"Солнечная дуга: {deg}°{mins:02d}'")

        planets = result["planets"]
        self.table_planets.setRowCount(len(planets))
        for r, p in enumerate(planets):
            values = [
                get_planet_name_ru(p["name"]),
                f"{p['longitude']:.2f}",
                get_sign_name_ru(p.get("sign", "")),
                f"{p.get('degree_in_sign', 0.0):.2f}",
            ]
            for c, v in enumerate(values):
                self.table_planets.setItem(r, c, QTableWidgetItem(v))

        aspects = result["aspects"]
        self.table_aspects.setRowCount(len(aspects))
        for r, a in enumerate(aspects):
            info = ASPECT_INFO.get(a["aspect"], {})
            values = [
                get_planet_name_ru(a["dir_planet"]),
                get_planet_name_ru(a["natal_point"]),
                info.get("name", a["aspect"]),
                f"{abs(a['orb']):.2f}",
                f"{a['score']:+d}",
            ]
            for c, v in enumerate(values):
                self.table_aspects.setItem(r, c, QTableWidgetItem(v))

        lines = ["Ключевые дирекционные аспекты:"]
        for a in aspects[:8]:
            info = ASPECT_INFO.get(a["aspect"], {})
            lines.append(
                f"• Дир. {get_planet_name_ru(a['dir_planet'])} "
                f"{info.get('phrase', 'аспект')} "
                f"{get_planet_name_ru(a['natal_point'])} "
                f"(орб {abs(a['orb']):.1f}) — {info.get('meaning', '')}")
        if not aspects:
            lines.append("• точных аспектов в заданных орбах нет")
        self._last_text = "\n".join(lines) + "\n\n" + DISCLAIMER
        self.text_summary.setPlainText(self._last_text)
