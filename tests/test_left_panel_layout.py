"""Геометрия панелей: пропорции, доступность контента, компактный список профилей."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QEventLoop, Qt, QTimer
from PyQt6.QtWidgets import QAbstractItemView, QApplication


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _drain(ms=150):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


@pytest.fixture
def window(qapp):
    from ui_qt.main_window import MainWindow
    win = MainWindow()
    win.resize(1400, 900)
    win.show()
    _drain(250)
    yield win
    win._time_slider.stop()
    win._background.cancel()
    win._background.wait(3000)
    win.deleteLater()


def test_left_pane_not_collapsed_at_startup(window):
    assert window._main_splitter.widget(0).width() >= 240


def test_right_pane_does_not_dominate(window):
    splitter = window._main_splitter
    assert splitter.sizes()[2] <= sum(splitter.sizes()) * 0.40


def test_center_pane_gets_most_space(window):
    sizes = window._main_splitter.sizes()
    assert sizes[1] >= sizes[0] and sizes[1] >= sizes[2]


def test_sections_have_no_fixed_height(window):
    window.resize(900, 600)
    _drain()
    for group in window._birth_input_panel._eq_groups:
        assert group.maximumHeight() == 16777215


def test_content_reachable_when_narrow(window):
    """Панель либо влезает, либо даёт прокрутку — молчаливой обрезки быть не должно."""
    window.resize(900, 620)
    _drain(250)
    scroll = window._birth_scroll
    viewport = scroll.viewport()
    panel = window._birth_input_panel
    if panel.width() > viewport.width() + 2:
        assert scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
        assert scroll.horizontalScrollBar().maximum() > 0,             "контент шире вьюпорта, но прокрутка недоступна"


def test_horizontal_policy_allows_access(window):
    assert (window._birth_scroll.horizontalScrollBarPolicy()
            == Qt.ScrollBarPolicy.ScrollBarAsNeeded)


def test_profile_list_shows_about_four_rows(window):
    views = window._profile_manager.findChildren(QAbstractItemView)
    assert views
    for view in views:
        row = view.fontMetrics().height() + 6
        assert view.height() <= 4 * row + 20
        assert view.height() >= 3 * row


def test_object_checkboxes_in_own_group(window):
    """Сетка галочек не должна стоять в строке формы с подписью слева."""
    panel = window._birth_input_panel
    group = panel.chk_asteroids.parentWidget()
    assert group is not None
    assert group.layout() is not None
    assert panel.chk_vertex.parentWidget() is group
