"""
Панель транзитов — вкладка "Транзиты" (итерация 22).

Не импортирует эфемериды: карту неба строит вызывающий код через get_sky.
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QComboBox, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QTextBrowser, QGroupBox,
    QHeaderView, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import QDate
from PyQt6.QtCore import pyqtSignal

from astro_core.constants import get_planet_name_ru
from astro_core.interpretations import ASPECT_INFO, DISCLAIMER
from astro_core.transits_daily import scan_periods, summarize_transits, transit_aspects


class TransitsPanel(QWidget):
    """Транзиты на дату и периоды действия аспектов."""

    help_requested = pyqtSignal(str)

    def __init__(self, get_chart, get_sky, parent=None):
        super().__init__(parent)
        self._get_chart = get_chart
        self._get_sky = get_sky
        self._last_summary = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        group = QGroupBox("🌠 Транзиты (текущее небо)")
        gl = QHBoxLayout(group)
        gl.addWidget(QLabel("Дата:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        gl.addWidget(self.date_edit)
        gl.addWidget(QLabel("Период:"))
        self.combo_days = QComboBox()
        for label, days in [("сегодня", 1), ("7 дней", 7), ("30 дней", 30), ("90 дней", 90)]:
            self.combo_days.addItem(label, days)
        gl.addWidget(self.combo_days)
        self.btn_calculate = QPushButton("🌠 Рассчитать")
        self.btn_calculate.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_calculate.clicked.connect(self._on_calculate)
        gl.addWidget(self.btn_calculate)
        self.btn_help = QPushButton("📖")
        self.btn_help.setToolTip("База Знаний: Транзиты")
        self.btn_help.clicked.connect(lambda _=False: self.help_requested.emit("Транзиты"))
        gl.addWidget(self.btn_help)
        self.btn_save = QPushButton("💾 Отчёт")
        self.btn_save.clicked.connect(self._on_save)
        gl.addWidget(self.btn_save)
        layout.addWidget(group)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Транзит", "Натальная точка", "Аспект", "Орб", "Баллы"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.table_periods = QTableWidget(0, 6)
        self.table_periods.setHorizontalHeaderLabels(
            ["Транзит", "Натальная точка", "Аспект", "Начало", "Конец", "Точно"])
        self.table_periods.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_periods.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_periods, 1)

        self.text_summary = QTextBrowser()
        layout.addWidget(self.text_summary, 1)

    def _selected_date(self):
        qd = self.date_edit.date()
        return date(qd.year(), qd.month(), qd.day())

    def _on_calculate(self):
        chart = self._get_chart()
        if not chart:
            self.text_summary.setPlainText(
                "Нет натальной карты.\nСначала рассчитайте натальную карту, затем вернитесь к транзитам.")
            return
        d = self._selected_date()
        days = self.combo_days.currentData()
        sky = self._get_sky(chart, d)
        aspects = transit_aspects(chart, sky)
        periods = None
        if days > 1:
            periods = scan_periods(chart, d, days, lambda dd: self._get_sky(chart, dd))
        self._fill_table(aspects)
        self._fill_periods(periods or [])
        self._last_summary = summarize_transits(chart, aspects, d, periods) + "\n\n" + DISCLAIMER
        self.text_summary.setPlainText(self._last_summary)

    def _fill_table(self, aspects):
        self.table.setRowCount(len(aspects))
        for r, a in enumerate(aspects):
            info = ASPECT_INFO.get(a["aspect"], {})
            values = [
                get_planet_name_ru(a["transit_planet"]),
                get_planet_name_ru(a["natal_point"]),
                info.get("name", a["aspect"]),
                f"{abs(a['orb']):.2f}",
                f"{a['score']:+d}",
            ]
            for c, v in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(v))

    def _fill_periods(self, periods):
        self.table_periods.setRowCount(len(periods))
        for r, p in enumerate(periods):
            info = ASPECT_INFO.get(p["aspect"], {})
            values = [
                get_planet_name_ru(p["transit_planet"]),
                get_planet_name_ru(p["natal_point"]),
                info.get("name", p["aspect"]),
                p["start"].strftime("%Y-%m-%d"),
                p["end"].strftime("%Y-%m-%d"),
                p["exact_date"].strftime("%Y-%m-%d"),
            ]
            for c, v in enumerate(values):
                self.table_periods.setItem(r, c, QTableWidgetItem(v))

    def _on_save(self):
        if not self._last_summary:
            QMessageBox.information(self, "Отчёт", "Сначала рассчитайте транзиты.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "transits_report.txt", "Текстовые файлы (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._last_summary)
        QMessageBox.information(self, "Отчёт", f"Отчёт сохранён:\n{path}")
