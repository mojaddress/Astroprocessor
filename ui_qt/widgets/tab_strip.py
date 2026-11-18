"""Двухрядная полоса вкладок с общей горизонтальной прокруткой (TAB_STRIP_V1).

Стрелки прокручивают обе строки одновременно, потому что прокрутка одна:
две строки кнопок лежат в одном виджете внутри QScrollArea.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QButtonGroup, QGridLayout, QHBoxLayout, QPushButton,
                             QScrollArea, QWidget)

SHORT_TITLES = {
    "🌠 Транзиты дня": "Транз. дня",
    "Транзиты дня": "Транз. дня",
    "📖 Анализ": "Анализ",
    "🌀 Дирекции": "Дирекции",
    "☀️ Обращения": "Обращения",
    "🔗 Средние точки": "Сред. точки",
    "Средние точки": "Сред. точки",
    "🌙 День и часы": "День и часы",
    "День и часы": "День и часы",
}
ROW_COUNT = 2
BUTTON_HEIGHT = 22


class TabStrip(QWidget):
    """Кнопки-вкладки в две строки; выбор испускает tab_chosen(заголовок)."""

    tab_chosen = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        self.btn_left = QPushButton("◀")
        self.btn_right = QPushButton("▶")
        for button in (self.btn_left, self.btn_right):
            button.setFixedWidth(18)
            button.setFixedHeight(2 * BUTTON_HEIGHT + 6)
            button.setToolTip("Прокрутить обе строки вкладок")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setFixedHeight(2 * BUTTON_HEIGHT + 6)

        self.inner = QWidget()
        self.grid = QGridLayout(self.inner)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(2)
        self.scroll.setWidget(self.inner)

        outer.addWidget(self.btn_left)
        outer.addWidget(self.scroll, 1)
        outer.addWidget(self.btn_right)
        self.btn_left.clicked.connect(lambda: self.scroll_by(-1))
        self.btn_right.clicked.connect(lambda: self.scroll_by(1))

    def add_tab(self, title):
        index = len(self._buttons)
        row = index % ROW_COUNT
        col = index // ROW_COUNT
        button = QPushButton(SHORT_TITLES.get(title, title))
        button.setToolTip(title)
        button.setCheckable(True)
        button.setFixedHeight(BUTTON_HEIGHT)
        button.setMinimumWidth(0)
        button.clicked.connect(lambda _=False, t=title: self.tab_chosen.emit(t))
        self._group.addButton(button)
        self.grid.addWidget(button, row, col)
        self._buttons[title] = button
        return button

    def select(self, title):
        button = self._buttons.get(title)
        if button is not None and not button.isChecked():
            button.setChecked(True)

    def scroll_by(self, direction):
        bar = self.scroll.horizontalScrollBar()
        step = max(40, self.scroll.viewport().width() // 2)
        bar.setValue(bar.value() + direction * step)

    def titles(self):
        return list(self._buttons)
