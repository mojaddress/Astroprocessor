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
        """Одна строка управления + строка ползунка (SLIDER_ONE_ROW_V1)."""
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 2, 6, 2)
        root.setSpacing(3)

        controls = QHBoxLayout()
        controls.setSpacing(4)
        self.btn_start = QPushButton("⏮")
        self.btn_prev = QPushButton("◀")
        self.btn_play = QPushButton("▶ Пуск")
        self.btn_next = QPushButton("▶|")
        self.btn_end = QPushButton("⏭")
        for button, tip, width in (
                (self.btn_start, "В начало окна", 26),
                (self.btn_prev, "Шаг назад", 26),
                (self.btn_play, "Анимация транзитов", 66),
                (self.btn_next, "Шаг вперёд", 26),
                (self.btn_end, "В конец окна", 26)):
            button.setToolTip(tip)
            button.setFixedWidth(width)
            button.setFixedHeight(24)
            controls.addWidget(button)

        self.combo_window = QComboBox()
        for title, _days in self.WINDOWS:
            self.combo_window.addItem(title)
        self.combo_window.setCurrentIndex(1)
        self.combo_window.setToolTip("Диапазон окна времени")
        self.combo_step = QComboBox()
        for title, _days in self.STEPS:
            self.combo_step.addItem(title)
        self.combo_step.setToolTip("Шаг перемещения")
        self.combo_speed = QComboBox()
        for title, _ms in self.SPEEDS:
            self.combo_speed.addItem(title)
        self.combo_speed.setCurrentIndex(1)
        self.combo_speed.setToolTip("Скорость анимации")
        for combo in (self.combo_window, self.combo_step, self.combo_speed):
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(4)
            combo.setFixedHeight(24)
            controls.addWidget(combo)

        controls.addStretch(1)
        self.lbl_date = QLabel("")
        self.lbl_date.setMinimumWidth(66)
        self.lbl_date.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        controls.addWidget(self.lbl_date)
        root.addLayout(controls)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setSingleStep(1)
        self.slider.setFixedHeight(18)
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
        self.btn_play.setText("▶ Пуск")

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
        self._refresh_label()  # SLIDER_SILENT_V1

    def _apply_speed(self):
        self._timer.setInterval(self.SPEEDS[self.combo_speed.currentIndex()][1])

    def _step_days(self) -> int:
        return self.STEPS[self.combo_step.currentIndex()][1]

    def _set_value(self, value: int):
        self.slider.setValue(max(0, min(self.slider.maximum(), int(value))))

    def _step(self, direction: int):
        self._set_value(self.slider.value() + direction * self._step_days())

    def _refresh_label(self):
        """Обновляет подпись даты БЕЗ сигнала (SLIDER_SILENT_V1).

        Программная установка точки отсчёта или окна - не действие
        пользователя, поэтому перерисовку транзитов не запускает.
        """
        self.lbl_date.setText(self.current_date().toString("dd.MM.yyyy"))

    def _on_value(self, value: int):
        date = self._anchor.addDays(int(value))
        self.lbl_date.setText(date.toString("dd.MM.yyyy"))
        self.date_changed.emit(date)

    def _tick(self):
        if self.slider.value() >= self.slider.maximum():
            self.stop()
            return
        self._step(1)
