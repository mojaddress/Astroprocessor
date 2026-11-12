"""Провайдер цветов полотна карты, согласованный с темой интерфейса.  # CHART_THEME_V1

Фон и чернила по умолчанию берутся из режима темы; пользовательские цвета
профилей отображения сохраняются, но адаптируются по яркости на тёмном фоне.
Экспорт PNG следует текущей теме (WYSIWYG).
"""
from __future__ import annotations

from PyQt6.QtGui import QColor

_dark = False
_rendered = False


def set_dark(dark: bool) -> None:
    global _dark
    _dark = bool(dark)


def is_dark() -> bool:
    return _dark


def mark_rendered() -> None:
    global _rendered
    _rendered = True


def was_rendered() -> bool:
    return _rendered


def bg() -> QColor:
    """Фон полотна карты; заодно отмечает, что карта рисовалась."""
    mark_rendered()
    return QColor("#17181A") if _dark else QColor("white")


def ink_hex() -> str:
    return "#E8EAED" if _dark else "#000000"


def adapt(color: QColor) -> QColor:
    """На тёмной теме поднимает яркость слишком тёмных цветов.

    Прозрачные цвета не трогает. Идемпотентен: повторный вызов не меняет результат.
    На светлой теме возвращает исходный цвет без изменений.
    """
    if not _dark or color.alpha() == 0:
        return color
    h, s, v, a = color.getHsvF()
    if v < 0.55:
        out = QColor()
        out.setHsvF(h, s, 0.85, a)
        return out
    return color
