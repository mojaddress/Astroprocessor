"""Диалог управления файлами эфемерид (EPHE_GUI_V1).

Показывает состояние файлов, возможности продукта и умеет докачать
недостающее в фоне с прогрессом и отменой. Загрузка не блокирует UI.
"""
from __future__ import annotations

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices  # в PyQt6 сервисы живут в QtGui
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QHeaderView, QLabel,
                             QProgressBar, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout)

from astro_core import ephe_manager as em
from ui_qt.background import BackgroundRunner

STATE_LABELS = {"ok": "в порядке", "missing": "отсутствует",
                "changed": "сумма не совпала", "variant": "другая редакция"}


class EphemerisDialog(QDialog):
    def __init__(self, busy_check=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Файлы эфемерид")
        self.resize(660, 420)
        self._busy_check = busy_check or (lambda: False)
        self._runner = None
        self.changed = False

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Файлы Swiss Ephemeris лицензированы Astrodienst и не входят в "
            "дистрибутив. Скачайте их один раз — программа запомнит папку."))

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Файл", "Состояние", "Назначение"])
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.lbl_caps = QLabel("")
        self.lbl_caps.setWordWrap(True)
        layout.addWidget(self.lbl_caps)

        self.bar = QProgressBar()
        self.bar.setVisible(False)
        layout.addWidget(self.bar)
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        buttons = QHBoxLayout()
        self.btn_download = QPushButton("⬇ Скачать недостающие")
        self.btn_check = QPushButton("🔄 Проверить")
        self.btn_folder = QPushButton("📁 Открыть папку")
        self.btn_close = QPushButton("Закрыть")
        for button in (self.btn_download, self.btn_check, self.btn_folder,
                       self.btn_close):
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.btn_download.clicked.connect(self._on_download)
        self.btn_check.clicked.connect(self.refresh)
        self.btn_folder.clicked.connect(self._on_folder)
        self.btn_close.clicked.connect(self.accept)
        self.refresh()

    def refresh(self):
        info = em.summary()
        self.table.setRowCount(len(info["files"]))
        for row, entry in enumerate(info["files"]):
            self.table.setItem(row, 0, QTableWidgetItem(entry["name"]))
            self.table.setItem(
                row, 1, QTableWidgetItem(STATE_LABELS.get(entry["state"], entry["state"])))
            self.table.setItem(row, 2, QTableWidgetItem(entry["purpose"]))
        caps = info["capabilities"]
        self.lbl_caps.setText(
            "Точность планет: "
            + ("высокая" if caps["high_precision_planets"] else "пониженная (Moshier)")
            + "; Хирон/астероиды: " + ("да" if caps["chiron_and_asteroids"] else "нет")
            + "; Селена/Прозерпина: " + ("да" if caps["fictitious_points"] else "нет"))
        self.lbl_status.setText(f"Папка: {info['folder']}")
        self.table.resizeColumnsToContents()

    def _on_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(em.resolve_folder())))

    def _on_download(self):
        if self._busy_check():
            self.lbl_status.setText("Идёт другой расчёт — дождитесь окончания.")
            return
        self.btn_download.setEnabled(False)
        self.bar.setVisible(True)
        self.bar.setRange(0, 100)
        self._runner = BackgroundRunner(self)
        self._runner.submit(self._task, on_done=self._done, on_progress=self._progress,
                            on_error=self._error, on_finished=self._finished)

    def _task(self, token, report):
        return em.download_missing(progress=report, cancel=token.raise_if_cancelled)

    def _progress(self, percent, message):
        self.bar.setValue(int(percent))

    def _done(self, report):
        self.changed = bool(report.get("downloaded"))
        if report.get("failed"):
            self.lbl_status.setText("Ошибки: " + "; ".join(report["failed"].values()))
        else:
            em.apply_path()
            self.lbl_status.setText("Готово. Файлы подключены.")
        self.refresh()

    def _error(self, text):
        self.lbl_status.setText(f"Ошибка загрузки: {text}")

    def _finished(self):
        self.bar.setVisible(False)
        self.btn_download.setEnabled(True)
        self._runner = None
