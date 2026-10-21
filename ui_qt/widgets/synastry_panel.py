"""
Synastry Panel — вкладка правой панели для анализа совместимости.

Показывает: числовую оценку, таблицу межкартовых аспектов
и текстовую интерпретацию из локальной базы (итерация 21).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTextBrowser, QProgressBar, QGroupBox,
    QHeaderView,
)
from PyQt6.QtCore import pyqtSignal

from astro_core.constants import get_planet_name_ru
from astro_core.interpretations import ASPECT_INFO, DISCLAIMER, summarize_synastry


class SynastryPanel(QWidget):
    """Панель синастрии: выбор второго человека и результаты."""

    calculate_requested = pyqtSignal(str)
    help_requested = pyqtSignal(str)  # имя профиля второго человека

    def __init__(self, profile_controller, parent=None):
        super().__init__(parent)
        self._profile_controller = profile_controller
        self._init_ui()
        self.refresh_profiles()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        group = QGroupBox("💑 Синастрия (совместимость)")
        gl = QVBoxLayout(group)

        gl.addWidget(QLabel("Второй человек (профиль):"))
        row = QHBoxLayout()
        self.combo_person_b = QComboBox()
        self.combo_person_b.setPlaceholderText("— выберите профиль —")
        btn_refresh = QPushButton("↻")
        btn_refresh.setFixedWidth(32)
        btn_refresh.clicked.connect(self.refresh_profiles)
        row.addWidget(self.combo_person_b, 1)
        row.addWidget(btn_refresh)
        gl.addLayout(row)

        self.btn_calculate = QPushButton("💑 Рассчитать совместимость")
        self.btn_calculate.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_calculate.clicked.connect(self._on_calculate)
        gl.addWidget(self.btn_calculate)
        self.btn_help = QPushButton("📖")
        self.btn_help.setToolTip("База Знаний: Синастрия")
        self.btn_help.clicked.connect(lambda _=False: self.help_requested.emit("Синастрия"))
        gl.addWidget(self.btn_help)

        self.lbl_score = QLabel("Оценка: —")
        self.lbl_score.setStyleSheet("font-size: 14px; font-weight: bold;")
        gl.addWidget(self.lbl_score)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%v%")
        gl.addWidget(self.progress)

        layout.addWidget(group)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Человек A", "Человек B", "Аспект", "Орб", "Баллы"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.text_summary = QTextBrowser()
        self.text_summary.setOpenExternalLinks(False)
        layout.addWidget(self.text_summary, 1)

    def refresh_profiles(self):
        self.combo_person_b.clear()
        try:
            profiles = self._profile_controller.list_profiles()
            for p in profiles:
                self.combo_person_b.addItem(p.name)
        except Exception:
            pass

    def _on_calculate(self):
        self.calculate_requested.emit(self.combo_person_b.currentText())

    def set_results(self, result):
        """Заполняет панель результатом SynastryResult."""
        self.lbl_score.setText(
            f"Совместимость: {result.compatibility_percentage:.0f}% "
            f"(баллы: {result.total_score:+d})")
        self.progress.setValue(int(round(result.compatibility_percentage)))

        self.table.setRowCount(len(result.aspects))
        for r, a in enumerate(result.aspects):
            info = ASPECT_INFO.get(a["aspect"], {})
            values = [
                f"{get_planet_name_ru(a['point_a'])} ({a['point_a_chart']})",
                f"{get_planet_name_ru(a['point_b'])} ({a['point_b_chart']})",
                info.get("name", a["aspect"]),
                f"{a['orb']:.2f}",
                f"{a['score']:+d}",
            ]
            for c, v in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(v))

        self.text_summary.setPlainText(
            summarize_synastry(result.aspects, result.chart_a_name,
                               result.chart_b_name)
            + "\n\n" + DISCLAIMER)