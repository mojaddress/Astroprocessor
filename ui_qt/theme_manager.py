"""Управление темой оформления: Светлая / Тёмная / Системная.

Причина появления модуля: Qt >= 6.5 следует системной теме Windows,
а продукту нужен управляемый вид (выбор по времени суток).
По умолчанию - "system" (поведение Qt без переопределения).

Хранение выбора: персональный ini-файл пользователя (QSettings, IniFormat).
Совместимость: если у Qt нет setColorScheme (Qt < 6.8) - откат на QPalette.
"""
from __future__ import annotations

from ui_qt import chart_theme  # CHART_THEME_V1
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QActionGroup, QColor, QPalette
from PyQt6.QtWidgets import QApplication, QMenu, QPushButton

THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_SYSTEM = "system"
THEME_CHOICES = (THEME_LIGHT, THEME_DARK, THEME_SYSTEM)
DEFAULT_THEME = THEME_SYSTEM

_LABELS = {
    THEME_LIGHT: "Светлая",
    THEME_DARK: "Тёмная",
    THEME_SYSTEM: "Системная",
}

_ORG = "AstroProcessor"
_APP_NAME = "Theme"
_KEY = "mode"

_ORIGINAL_STYLE: str | None = None


def _settings() -> QSettings:
    return QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, _ORG, _APP_NAME)


def load_theme_mode() -> str:
    """Читает выбранную тему; при отсутствии или мусоре - системная."""
    mode = str(_settings().value(_KEY, DEFAULT_THEME)).lower()
    return mode if mode in THEME_CHOICES else DEFAULT_THEME


def save_theme_mode(mode: str) -> None:
    if mode not in THEME_CHOICES:
        raise ValueError(f"Неизвестная тема: {mode!r}")
    _settings().setValue(_KEY, mode)


def _palette(light: bool) -> QPalette:
    p = QPalette()
    if light:
        window, base, text = "#F0F0F0", "#FFFFFF", "#000000"
        button, highlight, tooltip = "#F0F0F0", "#306EFF", "#FFFFDC"
        link, disabled = "#0000EE", "#808080"
    else:
        window, base, text = "#202124", "#17181A", "#E8EAED"
        button, highlight, tooltip = "#2A2B2E", "#2A82DA", "#3A3A3A"
        link, disabled = "#7CB8FF", "#77787B"
    p.setColor(QPalette.ColorRole.Window, QColor(window))
    p.setColor(QPalette.ColorRole.WindowText, QColor(text))
    p.setColor(QPalette.ColorRole.Base, QColor(base))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(window))
    p.setColor(QPalette.ColorRole.Text, QColor(text))
    p.setColor(QPalette.ColorRole.Button, QColor(button))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(text))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(tooltip))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(text))
    p.setColor(QPalette.ColorRole.Highlight, QColor(highlight))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.ColorRole.Link, QColor(link))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(disabled))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(disabled))
    return p


def _system_is_dark(app: QApplication) -> bool:
    """True, если системная тема Windows сейчас тёмная (Qt >= 6.5)."""
    color_scheme = getattr(Qt, "ColorScheme", None)
    if color_scheme is None:
        return False
    try:
        return app.styleHints().colorScheme() == color_scheme.Dark
    except Exception:
        return False


def apply_theme(app: QApplication, mode: str) -> None:
    """Применяет тему к работающему приложению; безопасно вызывать при переключении.  # QT_THEME_V3

    Все три режима ставят стиль и палитру явно (Fusion + QPalette):
    поведение одинаково на Qt 6.4..6.12+ и не зависит от того, уважает ли
    стиль переопределение colorScheme. Избегает "закрепления" палитры,
    которое ранее блокировало переключение.
    "Системная" = совпасть с текущей схемой Windows на момент применения.
    """
    global _ORIGINAL_STYLE
    if mode not in THEME_CHOICES:
        mode = DEFAULT_THEME
    if _ORIGINAL_STYLE is None:
        _ORIGINAL_STYLE = app.style().objectName()
    if mode == THEME_SYSTEM:
        mode = THEME_DARK if _system_is_dark(app) else THEME_LIGHT
    chart_theme.set_dark(mode == THEME_DARK)
    app.setStyle("Fusion")
    app.setPalette(_palette(mode == THEME_LIGHT))
    for widget in app.allWidgets():
        widget.update()
    app.processEvents()
    if chart_theme.was_rendered():
        for widget in app.allWidgets():
            if isinstance(widget, QPushButton) and "Рассчитать карту" in widget.text():
                widget.click()
                break


def add_theme_menu(main_window) -> QMenu:
    """Добавляет меню "Тема" в меню-бар окна с тремя переключаемыми пунктами."""
    menu = QMenu("Тема", main_window)
    group = QActionGroup(menu)
    group.setExclusive(True)
    actions = {}
    for mode in (THEME_LIGHT, THEME_DARK, THEME_SYSTEM):
        action = menu.addAction(_LABELS[mode])
        action.setCheckable(True)
        group.addAction(action)
        actions[mode] = action

    def _on_trigger() -> None:
        mode = next(m for m, a in actions.items() if a.isChecked())
        save_theme_mode(mode)
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, mode)

    for action in actions.values():
        action.triggered.connect(_on_trigger)

    actions[load_theme_mode()].setChecked(True)
    main_window.menuBar().addMenu(menu)
    return menu