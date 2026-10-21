"""
Диалог «База Знаний»: живой поиск, категории, статьи (итерация 29).
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QTextBrowser,
    QLabel, QDialogButtonBox,
)

from astro_core.knowledge_base import KB_ARTICLES, categories, search_articles


def _render(text: str) -> str:
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("## "):
            out.append(f"<h3>{s[3:]}</h3>")
        elif s.startswith("- "):
            out.append(f"<li>{s[2:]}</li>")
        else:
            out.append(f"<p>{s}</p>")
    return "".join(out)


class KnowledgeDialog(QDialog):
    """База Знаний: поиск сверху, категории и статьи слева, текст справа."""

    def __init__(self, parent=None, initial_query=""):
        super().__init__(parent)
        self.setWindowTitle("База Знаний")
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Поиск: название, термин, тег…")
        self.edit_search.textChanged.connect(self._refresh_list)
        layout.addWidget(self.edit_search)
        body = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Категории:"))
        self.list_cats = QListWidget()
        self.list_cats.currentTextChanged.connect(self._refresh_list)
        left.addWidget(self.list_cats)
        left.addWidget(QLabel("Статьи:"))
        self.list_articles = QListWidget()
        self.list_articles.currentItemChanged.connect(self._show_article)
        left.addWidget(self.list_articles)
        body.addLayout(left, 2)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        body.addWidget(self.browser, 3)
        layout.addLayout(body, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.list_cats.addItems(["Все"] + categories())
        if initial_query == "GLOSSARY":
            cats = categories()
            if "Глоссарий" in cats:
                self.list_cats.setCurrentRow(1 + cats.index("Глоссарий"))
        elif initial_query:
            self.edit_search.setText(initial_query)
        self._refresh_list()

    def _filtered(self):
        q = self.edit_search.text().strip()
        cat = self.list_cats.currentText()
        arts = search_articles(q) if q else list(KB_ARTICLES)
        if cat and cat != "Все":
            arts = [a for a in arts if a["category"] == cat]
        return arts

    def _refresh_list(self, _=None):
        self.list_articles.clear()
        for a in self._filtered():
            self.list_articles.addItem(f'{a["title"]}  ·  {a["category"]}')
        if self.list_articles.count():
            self.list_articles.setCurrentRow(0)
        else:
            self.browser.setHtml("<p>Ничего не найдено. Попробуйте другой запрос "
                                 "или категорию «Все».</p>")

    def _show_article(self, _cur=None, _prev=None):
        row = self.list_articles.currentRow()
        arts = self._filtered()
        if 0 <= row < len(arts):
            a = arts[row]
            self.browser.setHtml(
                f"<h2>{a['title']}</h2>"
                f"<p><i>{a['category']} · теги: {', '.join(a['tags'])}</i></p>"
                + _render(a["text"]))
