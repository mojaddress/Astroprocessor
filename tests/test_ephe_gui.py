"""GUI-менеджер эфемерид: состав, блокировка при занятом фоне, подсказка."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication

from ui_qt.dialogs.ephemeris_dialog import EphemerisDialog


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _drain(ms=200):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_dialog_lists_four_files(qapp):
    dialog = EphemerisDialog()
    try:
        assert dialog.table.rowCount() == 4
        assert "Точность планет" in dialog.lbl_caps.text()
        assert dialog.lbl_status.text().startswith("Папка:")
    finally:
        dialog.close()
        dialog.deleteLater()


def test_download_blocked_when_busy(qapp):
    dialog = EphemerisDialog(busy_check=lambda: True)
    try:
        dialog._on_download()
        assert "дождитесь" in dialog.lbl_status.text()
        assert dialog._runner is None
    finally:
        dialog.close()
        dialog.deleteLater()


def test_settings_menu_has_ephe_action(qapp):
    from ui_qt.main_window import MainWindow
    win = MainWindow()
    try:
        texts = [action.text() for action in win.findChildren(QAction)]
        assert any("Файлы эфемерид" in text for text in texts)
    finally:
        win._time_slider.stop()
        win._background.cancel()
        win._background.wait(3000)
        win.deleteLater()


def test_first_run_prompt_sets_flag(qapp):
    from ui_qt.main_window import MainWindow
    win = MainWindow()
    win.resize(1200, 800)
    win.show()
    _drain(250)
    try:
        win._maybe_prompt_ephemeris()
        assert win._ephe_prompted is True
        for dialog in win.findChildren(EphemerisDialog):
            dialog.close()
    finally:
        win._time_slider.stop()
        win._background.cancel()
        win._background.wait(3000)
        win.deleteLater()
