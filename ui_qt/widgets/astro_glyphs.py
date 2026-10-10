"""
Векторные глифы астрономических объектов.

Решает проблему отсутствия глифов в системных шрифтах:
символы рисуются геометрией (QPainterPath), а не текстом.
Каждый глиф построен в условном квадрате 0..100 (stroke-стиль),
масштабируется вызывающим кодом.
"""

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainterPath

# Толщина штриха в единицах квадрата 100x100
GLYPH_STROKE = 7.0


def _circle(path: QPainterPath, cx, cy, r):
    path.addEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))


def glyph_sun():
    p = QPainterPath()
    _circle(p, 50, 50, 28)
    fills = [QRectF(50 - 7, 50 - 7, 14, 14)]
    return p, fills


def glyph_moon():
    p = QPainterPath()
    p.moveTo(58, 20)
    p.quadTo(18, 50, 58, 80)
    p.quadTo(38, 50, 58, 20)
    return p, []


def glyph_mercury():
    p = QPainterPath()
    p.moveTo(32, 24)
    p.quadTo(50, 46, 68, 24)          # рожки
    _circle(p, 50, 52, 16)           # круг
    p.moveTo(50, 68); p.lineTo(50, 90)   # крест
    p.moveTo(38, 80); p.lineTo(62, 80)
    return p, []


def glyph_venus():
    p = QPainterPath()
    _circle(p, 50, 38, 17)
    p.moveTo(50, 55); p.lineTo(50, 88)
    p.moveTo(36, 72); p.lineTo(64, 72)
    return p, []


def glyph_mars():
    p = QPainterPath()
    _circle(p, 40, 60, 17)
    p.moveTo(52, 48); p.lineTo(76, 24)
    p.moveTo(76, 24); p.lineTo(58, 24)
    p.moveTo(76, 24); p.lineTo(76, 42)
    return p, []


def glyph_jupiter():
    p = QPainterPath()
    p.moveTo(60, 20); p.lineTo(36, 58)
    p.moveTo(36, 58); p.lineTo(76, 58)
    p.moveTo(60, 20); p.lineTo(60, 86)
    return p, []


def glyph_saturn():
    p = QPainterPath()
    p.moveTo(40, 12); p.lineTo(40, 50)     # стержень с крестом
    p.moveTo(30, 24); p.lineTo(50, 24)
    p.moveTo(40, 50)                       # крюк
    p.quadTo(40, 66, 54, 66)
    p.quadTo(66, 66, 66, 54)
    p.moveTo(66, 54); p.lineTo(66, 88)     # правая нога
    return p, []


def glyph_uranus():
    p = QPainterPath()
    _circle(p, 50, 64, 16)
    p.moveTo(50, 48); p.lineTo(50, 30)
    p.moveTo(36, 12); p.lineTo(36, 40)
    p.moveTo(64, 12); p.lineTo(64, 40)
    p.moveTo(36, 28); p.lineTo(64, 28)
    return p, []


def glyph_neptune():
    p = QPainterPath()
    p.moveTo(50, 88); p.lineTo(50, 34)
    p.moveTo(32, 12); p.quadTo(32, 34, 50, 34)
    p.moveTo(68, 12); p.quadTo(68, 34, 50, 34)
    p.moveTo(50, 12); p.lineTo(50, 34)
    return p, []


def glyph_pluto():
    p = QPainterPath()
    p.moveTo(34, 32); p.quadTo(50, 50, 66, 32)   # чаша
    _circle(p, 50, 58, 14)
    p.moveTo(50, 72); p.lineTo(50, 90)
    p.moveTo(40, 81); p.lineTo(60, 81)
    return p, []


def glyph_north_node():
    p = QPainterPath()
    p.moveTo(30, 68)
    p.quadTo(30, 26, 50, 26)
    p.quadTo(70, 26, 70, 68)
    p.moveTo(30, 68); p.lineTo(20, 68)
    p.moveTo(70, 68); p.lineTo(80, 68)
    return p, []


def glyph_south_node():
    p = QPainterPath()
    p.moveTo(30, 32)
    p.quadTo(30, 74, 50, 74)
    p.quadTo(70, 74, 70, 32)
    p.moveTo(30, 32); p.lineTo(20, 32)
    p.moveTo(70, 32); p.lineTo(80, 32)
    return p, []


def glyph_chiron():
    p = QPainterPath()
    _circle(p, 50, 28, 14)
    p.moveTo(50, 42); p.lineTo(50, 88)
    p.moveTo(50, 64); p.lineTo(66, 50)
    p.moveTo(58, 57); p.lineTo(66, 70)
    return p, []


def glyph_part_of_fortune():
    p = QPainterPath()
    _circle(p, 50, 50, 20)
    p.moveTo(30, 50); p.lineTo(70, 50)
    p.moveTo(50, 30); p.lineTo(50, 70)
    return p, []


GLYPH_BUILDERS = {
    "Sun": glyph_sun,
    "Moon": glyph_moon,
    "Mercury": glyph_mercury,
    "Venus": glyph_venus,
    "Mars": glyph_mars,
    "Jupiter": glyph_jupiter,
    "Saturn": glyph_saturn,
    "Uranus": glyph_uranus,
    "Neptune": glyph_neptune,
    "Pluto": glyph_pluto,
    "MeanNode": glyph_north_node,
    "TrueNode": glyph_north_node,
    "SouthNode": glyph_south_node,
    "Chiron": glyph_chiron,
    "PartOfFortune": glyph_part_of_fortune,
}


def get_glyph(name: str):
    """Возвращает (QPainterPath, list[QRectF]) или None, если глифа нет."""
    builder = GLYPH_BUILDERS.get(name)
    if builder is None:
        return None
    return builder()