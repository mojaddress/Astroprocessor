"""Двухрядная полоса вкладок правой панели."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication

from ui_qt.widgets.tab_strip import TabStrip


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _drain(ms=200):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_two_rows_layout():
    strip = TabStrip()
    for title in ["a", "b", "c", "d", "e", "f", "g", "h", "i"]:
        strip.add_tab(title)
    assert strip.grid.rowCount() == 2
    assert strip.grid.columnCount() == 5
    strip.deleteLater()


def test_click_emits_title():
    strip = TabStrip()
    strip.add_tab("Транзиты")
    strip.add_tab("Прогрессии")
    seen = []
    strip.tab_chosen.connect(seen.append)
    strip._buttons["Прогрессии"].click()
    assert seen == ["Прогрессии"]
    strip.deleteLater()


def test_select_checks_button():
    strip = TabStrip()
    strip.add_tab("a")
    strip.add_tab("b")
    strip.select("b")
    assert strip._buttons["b"].isChecked()
    assert not strip._buttons["a"].isChecked()
    strip.deleteLater()


def test_arrows_scroll_both_rows():
    strip = TabStrip()
    for index in range(12):
        strip.add_tab(f"very-long-title-{index}")
    strip.resize(200, 60)
    strip.show()
    _drain()
    bar = strip.scroll.horizontalScrollBar()
    assert bar.maximum() > 0, "контент шире вьюпорта, прокрутка нужна"
    before = bar.value()
    strip.btn_right.click()
    assert bar.value() > before
    strip.btn_left.click()
    assert bar.value() < bar.maximum()
    strip.deleteLater()


def test_main_window_uses_strip(qapp):
    from ui_qt.main_window import MainWindow
    win = MainWindow()
    win.resize(1400, 900)
    win.show()
    _drain(300)
    try:
        assert win._calc_tabs.tabBar().isHidden()
        assert len(win._tab_strip.titles()) == win._calc_tabs.count()
        target = win._calc_tabs.tabText(1)
        win._tab_strip._buttons[target].click()
        _drain()
        assert win._calc_tabs.tabText(win._calc_tabs.currentIndex()) == target
    finally:
        win._time_slider.stop()
        win._background.cancel()
        win._background.wait(3000)
        win.deleteLater()
