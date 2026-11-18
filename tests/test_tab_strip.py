"""Двухрядная полоса вкладок правой панели (CRASH_FIX_V1).

Каждый тест модуля требует живого QApplication: создание QWidget без него
аварийно завершает процесс без трейсбека, что выглядело как «зависание».
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication

from ui_qt.widgets.tab_strip import TabStrip

HANG_TIMEOUT_MS = 5000


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _needs_app(qapp):
    """Страховка: ни один тест модуля не создаёт виджет без приложения."""
    return qapp


def _drain(ms=150):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    QTimer.singleShot(HANG_TIMEOUT_MS, loop.quit)  # защита от зависания
    loop.exec()


def test_two_rows_layout(qapp):
    strip = TabStrip()
    for title in ["a", "b", "c", "d", "e", "f", "g", "h", "i"]:
        strip.add_tab(title)
    assert strip.grid.rowCount() == 2
    assert strip.grid.columnCount() == 5
    strip.deleteLater()


def test_click_emits_title(qapp):
    strip = TabStrip()
    strip.add_tab("Транзиты")
    strip.add_tab("Прогрессии")
    seen = []
    strip.tab_chosen.connect(seen.append)
    strip._buttons["Прогрессии"].click()
    assert seen == ["Прогрессии"]
    strip.deleteLater()


def test_select_checks_button(qapp):
    strip = TabStrip()
    strip.add_tab("a")
    strip.add_tab("b")
    strip.select("b")
    assert strip._buttons["b"].isChecked()
    assert not strip._buttons["a"].isChecked()
    strip.deleteLater()


def test_arrows_scroll_both_rows(qapp):
    strip = TabStrip()
    for index in range(12):
        strip.add_tab(f"very-long-title-{index}")
    strip.resize(200, 60)
    strip.show()
    _drain()
    bar = strip.scroll.horizontalScrollBar()
    assert bar.maximum() > 0
    before = bar.value()
    strip.btn_right.click()
    assert bar.value() > before
    strip.btn_left.click()
    assert bar.value() < bar.maximum()
    strip.deleteLater()


def test_main_window_strip_has_same_count_as_tabs(qapp):
    """Без show(): проверяем соответствие полосы и вкладок, не запуская каскады."""
    from ui_qt.main_window import MainWindow

    win = MainWindow()
    _drain(100)
    try:
        if hasattr(win, "_populate_tab_strip"):
            win._populate_tab_strip()
        _drain(100)
        assert len(win._tab_strip.titles()) == win._calc_tabs.count()
        for index in range(win._calc_tabs.count()):
            title = win._calc_tabs.tabText(index)
            assert title in win._tab_strip._buttons, f"вкладка {title!r} не в полосе"
    finally:
        win._time_slider.stop()
        win._background.cancel()
        win._background.wait(3000)
        win.deleteLater()
        _drain(200)