"""Ползунок времени: плавная динамика транзитной карты (TIME_SLIDER_V1).

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
