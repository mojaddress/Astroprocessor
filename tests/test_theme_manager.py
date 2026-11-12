"""Тесты ui_qt.theme_manager: темы Светлая/Тёмная/Системная."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from ui_qt.theme_manager import (
    DEFAULT_THEME,
    THEME_CHOICES,
    apply_theme,
    load_theme_mode,
    save_theme_mode,
)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path):
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    yield


def test_default_is_system(qapp):
    assert load_theme_mode() == DEFAULT_THEME == "system"


def test_save_load_roundtrip(qapp):
    for mode in THEME_CHOICES:
        save_theme_mode(mode)
        assert load_theme_mode() == mode


def test_invalid_mode_rejected(qapp):
    with pytest.raises(ValueError):
        save_theme_mode("neon")


def test_corrupted_value_falls_back_to_default(qapp):
    QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
              "AstroProcessor", "Theme").setValue("mode", "garbage")
    assert load_theme_mode() == DEFAULT_THEME


def test_apply_theme_all_modes_no_crash(qapp):
    for mode in THEME_CHOICES:
        apply_theme(qapp, mode)
    apply_theme(qapp, "garbage")  # деградация до системной без падения