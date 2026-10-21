"""Итерация 29: структура и поиск Базы Знаний + smoke диалога."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from astro_core.knowledge_base import KB_ARTICLES, categories, get_article, search_articles


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication(sys.argv)


def test_kb_structure():
    ids = [a["id"] for a in KB_ARTICLES]
    assert len(ids) == len(set(ids))
    for a in KB_ARTICLES:
        assert a["id"] and a["category"] and a["title"] and a["text"]
        assert isinstance(a["tags"], list) and a["tags"]


def test_kb_search_directions():
    found = search_articles("дирекции")
    assert any(a["id"] == "directions" for a in found)


def test_kb_search_orb():
    assert search_articles("орб")


def test_kb_categories_include_glossary():
    assert "Глоссарий" in categories()


def test_kb_get_article():
    assert get_article("planet-sun") is not None
    assert get_article("no-such-id") is None


def test_dialog_smoke(app):
    from ui_qt.widgets.knowledge_dialog import KnowledgeDialog
    dlg = KnowledgeDialog(initial_query="Дирекции")
    assert dlg.list_articles.count() > 0
