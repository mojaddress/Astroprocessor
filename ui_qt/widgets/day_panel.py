"""Панель суточных циклов: планетарные часы, лунные сутки, фаза Луны (DAY_TAB_V1)."""
from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QAbstractItemView, QDateEdit, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from astro_core import day_cycles as dc
from astro_core.constants import get_planet_name_ru


class DayPanel(QWidget):
    """Планетарные часы и лунные сутки для даты и места."""

    def __init__(self, birth_provider, parent=None):
        super().__init__(parent)
        self._birth_provider = birth_provider
        self._hours = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        top = QGroupBox("Дата и место")
        form = QFormLayout(top)
        self.edit_date = QDateEdit()
        self.edit_date.setDate(QDate.currentDate())
        self.edit_date.setCalendarPopup(True)
        form.addRow("Дата:", self.edit_date)
        self.lbl_place = QLabel("место не задано")
        form.addRow("Место:", self.lbl_place)
        self.btn_calculate = QPushButton("🔄 Рассчитать день")
        self.btn_calculate.clicked.connect(self._on_calculate)
        form.addRow(self.btn_calculate)
        layout.addWidget(top)

        info = QGroupBox("Солнце и Луна")
        info_layout = QFormLayout(info)
        self.lbl_sun = QLabel("—")
        self.lbl_sun.setWordWrap(True)
        info_layout.addRow("Солнце:", self.lbl_sun)
        self.lbl_moon = QLabel("—")
        self.lbl_moon.setWordWrap(True)
        info_layout.addRow("Луна:", self.lbl_moon)
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["№", "Начало", "Конец", "Управитель", "Часть суток"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def _place(self):
        birth = self._birth_provider() if callable(self._birth_provider) else None
        if not birth:
            return None
        return (float(birth.get("latitude", 0.0)),
                float(birth.get("longitude", 0.0)),
                float(birth.get("utc_offset_hours", 0.0)),
                str(birth.get("city_name") or birth.get("name") or "место"))

    def _on_calculate(self):
        place = self._place()
        if place is None:
            self.lbl_place.setText("сначала рассчитайте натальную карту")
            self.table.setRowCount(0)
            return
        lat, lon, offset, name = place
        self.lbl_place.setText(f"{name} · {lat:.2f}, {lon:.2f} · UTC{offset:+.1f}")

        day = self.edit_date.date().toPyDate()
        midnight = datetime(day.year, day.month, day.day, 0, 0)
        events = dc.sun_events(midnight, lat, lon, offset)
        jd_noon = dc._jd_from_local(midnight, offset) + 0.5

        if events["polar"]:
            kind = "полярный день" if events["polar_day"] else "полярная ночь"
            self.lbl_sun.setText(f"{kind}: восход и заход в эту дату отсутствуют, "
                                 f"планетарные часы не определены")
            self._hours = []
            self.table.setRowCount(0)
        else:
            rise = dc._local_from_jd(events["rise"], offset)
            sunset = dc._local_from_jd(events["set"], offset)
            length = sunset - rise
            self.lbl_sun.setText(
                f"восход {rise:%H:%M}, заход {sunset:%H:%M}, "
                f"долгота дня {length.seconds // 3600} ч {(length.seconds % 3600) // 60} мин")
            self._hours = dc.planetary_hours(midnight, lat, lon, offset)
            self._fill_table(midnight, offset)

        self.lbl_moon.setText(
            f"лунные сутки {dc.lunar_day(jd_noon)}, фаза: {dc.moon_phase(jd_noon)}")

    def _fill_table(self, midnight, offset):
        now = datetime.now()
        same_day = now.date() == midnight.date()
        self.table.setRowCount(len(self._hours))
        for row, hour in enumerate(self._hours):
            values = [
                str(hour["index"]),
                f"{hour['start_local']:%H:%M}",
                f"{hour['end_local']:%H:%M}",
                get_planet_name_ru(hour["ruler"]),
                "день" if hour["kind"] == "day" else "ночь",
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                self.table.setItem(row, column, item)
            if same_day and hour["start_local"] <= now < hour["end_local"]:
                for column in range(5):
                    current = self.table.item(row, column)
                    font = current.font()
                    font.setBold(True)
                    current.setFont(font)
        self.table.resizeColumnsToContents()
