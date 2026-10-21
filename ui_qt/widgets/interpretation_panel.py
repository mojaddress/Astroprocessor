"""
Панель «Разбор» — целостные интерпретации натала и транзитов (итерация 23).

Локальная база интерпретаций + опциональное LLM-обогащение через .env.
Без ключа продукт работает полностью локально.
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser,
    QFileDialog, QMessageBox, QLabel,
)
from PyQt6.QtCore import pyqtSignal

from astro_core.interpretations import (
    DISCLAIMER, format_natal_profile, summarize_natal,
)
from astro_core.llm_client import ask_llm, llm_config
from astro_core.transits_daily import (
    scan_periods, summarize_transits, transit_aspects,
)


class InterpretationPanel(QWidget):
    """Целостный разбор: натал, транзиты, опционально LLM."""

    help_requested = pyqtSignal(str)

    def __init__(self, get_chart, get_sky, parent=None):
        super().__init__(parent)
        self._get_chart = get_chart
        self._get_sky = get_sky
        self._last_text = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        row = QHBoxLayout()
        self.btn_natal = QPushButton("📖 Разбор натала")
        self.btn_natal.clicked.connect(self._on_natal)
        row.addWidget(self.btn_natal)
        self.btn_transits = QPushButton("🌠 Разбор транзитов")
        self.btn_transits.clicked.connect(self._on_transits)
        row.addWidget(self.btn_transits)
        self.btn_llm = QPushButton("🤖 LLM (опция)")
        self.btn_llm.clicked.connect(self._on_llm)
        row.addWidget(self.btn_llm)
        self.btn_save = QPushButton("💾 Отчёт")
        self.btn_save.clicked.connect(self._on_save)
        row.addWidget(self.btn_save)
        self.btn_help = QPushButton("📖")
        self.btn_help.setToolTip("База Знаний: Анализ")
        self.btn_help.clicked.connect(lambda _=False: self.help_requested.emit("Анализ"))
        row.addWidget(self.btn_help)
        layout.addLayout(row)

        self.lbl_hint = QLabel("")
        self.lbl_hint.setWordWrap(True)
        layout.addWidget(self.lbl_hint)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        layout.addWidget(self.browser, 1)
        self._refresh_llm_hint()

    def _refresh_llm_hint(self):
        cfg = llm_config()
        if cfg:
            self.lbl_hint.setText(f"LLM подключена: {cfg['model']}")
        else:
            self.lbl_hint.setText(
                "LLM не настроена: разбор работает на локальной базе. "
                "Для подключения LLM создайте .env из .env.example "
                "(ключ не хранится в коде).")

    def _chart_or_hint(self):
        chart = self._get_chart()
        if not chart:
            self.browser.setPlainText(
                "Нет натальной карты.\nСначала рассчитайте натальную карту, "
                "затем вернитесь на вкладку «Анализ».")
            return None
        return chart

    def _on_natal(self):
        chart = self._chart_or_hint()
        if not chart:
            return
        text = (summarize_natal(chart) + "\n\n" + format_natal_profile(chart)
                + "\n\n" + DISCLAIMER)
        self._show(text)

    def _on_transits(self):
        chart = self._chart_or_hint()
        if not chart:
            return
        d = date.today()
        sky = self._get_sky(chart, d)
        aspects = transit_aspects(chart, sky)
        periods = scan_periods(chart, d, 30, lambda dd: self._get_sky(chart, dd))
        text = summarize_transits(chart, aspects, d, periods) + "\n\n" + DISCLAIMER
        self._show(text)

    def _on_llm(self):
        chart = self._chart_or_hint()
        if not chart:
            return
        cfg = llm_config()
        if not cfg:
            QMessageBox.information(
                self, "LLM не настроена",
                "Чтобы подключить LLM-разбор:\n1) скопируйте .env.example в .env;\n"
                "2) раскомментируйте и заполните один пресет (URL, модель, ключ);\n"
                "3) перезапустите приложение.\n"
                "Без ключа продукт полностью работает на локальной базе.")
            return
        local = summarize_natal(chart) + "\n\n" + format_natal_profile(chart)
        d = date.today()
        try:
            sky = self._get_sky(chart, d)
            aspects = transit_aspects(chart, sky)
            local += "\n\n" + summarize_transits(chart, aspects, d, None)
        except Exception:
            pass
        prompt = (
            "Составь связный рассказ на русском языке по данным ниже: "
            "1) характер и темперамент; 2) предрасположенности и подходящие сферы "
            "деятельности/профессии; 3) текущий транзитный период: чему благоприятствовать, "
            "что отложить. Не выдумывай факты вне данных, помечай неуверенные выводы.\n"
            "Данные:\n" + local)
        ok, result = ask_llm(prompt)
        if ok:
            self._show(
                f"🤖 LLM-разбор (модель: {cfg['model']}; экспериментально, не гарантия)\n\n"
                + result + "\n\n" + DISCLAIMER)
        else:
            self._show(
                "LLM-запрос не выполнен:\n" + result +
                "\n\nЛокальная база доступна кнопками «Разбор натала» и «Разбор транзитов».")

    def _show(self, text):
        self._last_text = text
        self.browser.setPlainText(text)

    def _on_save(self):
        if not self._last_text:
            QMessageBox.information(self, "Отчёт", "Сначала сформируйте разбор.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "interpretation.txt", "Текстовые файлы (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._last_text)
        QMessageBox.information(self, "Отчёт", f"Сохранено:\n{path}")
