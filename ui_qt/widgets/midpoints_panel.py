"""Панель анализа средних точек и планетарных картин (VXMP).

Не рисует ничего на колесе: 20 объектов дают 380 средних точек,
их вывал на карту сделал бы её нечитаемой. Анализ - в таблице.
"""
from __future__ import annotations

import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from astro_core.constants import get_planet_name_ru, get_sign_name_ru
from astro_core.midpoints import (
    DEFAULT_MIDPOINT_ORB, all_midpoints, occupied_midpoints,
)


class MidpointsPanel(QWidget):
    """Средние точки: все пары или только занятые (планетарные картины)."""

    def __init__(self, chart_provider, parent=None):
        super().__init__(parent)
        self._chart_provider = chart_provider
        self._rows = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        controls = QGroupBox("Параметры анализа")
        form = QFormLayout(controls)

        self.chk_only_occupied = QCheckBox("Только занятые (планетарные картины)")
        self.chk_only_occupied.setChecked(True)
        self.chk_only_occupied.setToolTip(
            "Показывать только те средние точки, на которых стоит третья планета")
        form.addRow(self.chk_only_occupied)

        self.spin_orb = QDoubleSpinBox()
        self.spin_orb.setRange(0.1, 5.0)
        self.spin_orb.setSingleStep(0.1)
        self.spin_orb.setDecimals(1)
        self.spin_orb.setValue(DEFAULT_MIDPOINT_ORB)
        self.spin_orb.setSuffix("°")
        form.addRow("Орб:", self.spin_orb)

        self.chk_opposite = QCheckBox("Учитывать дальнюю среднюю (+180°)")
        self.chk_opposite.setChecked(True)
        form.addRow(self.chk_opposite)

        layout.addWidget(controls)

        self.btn_calculate = QPushButton("🔄 Рассчитать средние точки")
        self.btn_calculate.clicked.connect(self._on_calculate)
        layout.addWidget(self.btn_calculate)

        self.lbl_summary = QLabel("Рассчитайте натальную карту, затем средние точки")
        self.lbl_summary.setWordWrap(True)
        layout.addWidget(self.lbl_summary)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.btn_export = QPushButton("📥 Экспорт JSON")
        self.btn_export.clicked.connect(self._on_export)
        layout.addWidget(self.btn_export)

        self.chk_only_occupied.stateChanged.connect(lambda _=0: self._refresh_if_ready())
        self.chk_opposite.stateChanged.connect(lambda _=0: self._refresh_if_ready())
        self.spin_orb.valueChanged.connect(lambda _=0.0: self._refresh_if_ready())

    def _refresh_if_ready(self):
        if self.table.rowCount() > 0:
            self._on_calculate()

    def _on_calculate(self):
        chart = self._chart_provider() if callable(self._chart_provider) else None
        if not chart:
            self.lbl_summary.setText("Сначала рассчитайте натальную карту")
            self.table.setRowCount(0)
            return

        objects = chart.get("objects", [])
        if self.chk_only_occupied.isChecked():
            self._rows = occupied_midpoints(
                objects, orb=self.spin_orb.value(),
                include_opposite=self.chk_opposite.isChecked())
            headers = ["Картина", "Планета", "Орб, '", "Долгота", "Знак", "Дайал 90°"]
        else:
            self._rows = all_midpoints(objects)
            headers = ["Пара", "Средняя", "Знак", "Дальняя (+180°)", "Дайал 90°"]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(self._rows))

        for row, entry in enumerate(self._rows):
            if self.chk_only_occupied.isChecked():
                minutes = int(round(float(entry["orb"]) * 60))
                values = [
                    f"{get_planet_name_ru(entry['a'])}/{get_planet_name_ru(entry['b'])}",
                    get_planet_name_ru(entry["planet"]),
                    str(minutes),
                    f"{entry['midpoint']:.3f}",
                    get_sign_name_ru(entry["sign"]),
                    f"{entry['dial90']:.3f}",
                ]
            else:
                values = [
                    f"{get_planet_name_ru(entry['a'])}/{get_planet_name_ru(entry['b'])}",
                    f"{entry['midpoint']:.3f}",
                    get_sign_name_ru(entry["sign"]),
                    f"{entry['opposite']:.3f}",
                    f"{entry['dial90']:.3f}",
                ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)

        self.table.resizeColumnsToContents()
        total_pairs = len(all_midpoints(objects))
        if self.chk_only_occupied.isChecked():
            self.lbl_summary.setText(
                f"Пар: {total_pairs}. Планетарных картин при орбе "
                f"{self.spin_orb.value():.1f}°: {len(self._rows)}")
        else:
            self.lbl_summary.setText(f"Пар средних точек: {total_pairs}")

    def _on_export(self):
        if not self._rows:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить средние точки", "midpoints.json", "JSON Files (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self._rows, handle, ensure_ascii=False, indent=2)
