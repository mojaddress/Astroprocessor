"""
Chart View — полностью векторный виджет астрологической карты.

Принципиальные отличия от прежней версии:
1. Никакого QPixmap и QSvgRenderer: карта строится как QGraphicsScene
   из векторных примитивов -> идеальное качество на любом зуме и DPI.
2. Символы планет/узлов/Хирона рисуются векторными глифами
   (astro_glyphs), а не текстом -> не зависят от установленных шрифтов.
3. set_svg() сохранён только для экспорта; если данные не переданы,
   виджет показывает диагностический баннер (видно, какой путь активен).
"""

import math
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsSimpleTextItem,
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QWheelEvent, QMouseEvent, QKeyEvent, QPainter, QPen, QBrush,
    QColor, QFont, QTransform, QImage,
)

from .astro_glyphs import get_glyph, GLYPH_STROKE

# Геометрия карты (доли от размера сцены)
SCENE_SIZE = 800
R_OUTER, R_ZODIAC = 0.440, 0.405
R_HOUSES, R_PLANETS, R_ASPECTS = 0.370, 0.325, 0.295

SIGN_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}
SIGNS = list(SIGN_SYMBOLS.keys())

PLANET_COLORS = {
    "Sun": "#FF8C00", "Moon": "#808080", "Mercury": "#DAA520",
    "Venus": "#32CD32", "Mars": "#FF4500", "Jupiter": "#9932CC",
    "Saturn": "#1C1C1C", "Uranus": "#00BFFF", "Neptune": "#008B8B",
    "Pluto": "#8B0000", "MeanNode": "#696969", "TrueNode": "#696969",
    "SouthNode": "#A9A9A9", "Chiron": "#8B4513",
}
ASPECT_COLORS = {
    "conjunction": "#FF4500", "sextile": "#1E90FF", "square": "#DC143C",
    "trine": "#228B22", "opposition": "#8A2BE2",
}


def lon_to_point(lon: float, radius: float, c: float) -> QPointF:
    a = math.radians(180.0 - lon)
    return QPointF(c + radius * math.cos(a), c - radius * math.sin(a))


def _angular_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return 360.0 - d if d > 180.0 else d


class ChartView(QGraphicsView):
    """Векторный интерактивный виджет карты (зум, панорама)."""

    chart_clicked = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._chart_data: Optional[Dict] = None
        self._transit_planets: List[Dict] = []
        self._transit_aspects: List[Dict] = []
        self._is_transit_mode = False
        self._svg_content = ""

        self._settings = {
            "show_planet_labels": True, "show_asteroid_labels": True,
            "show_node_labels": True, "show_angle_labels": True,
            "show_houses": True, "show_aspects": True,
            "label_mode": "symbols",
            "planet_colors": {}, "aspect_colors": {},
            "planet_dot_size": 6,
        }

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._zoom_factor = 1.0
        self._min_zoom, self._max_zoom = 0.1, 20.0

    # ------------------------------------------------------------ API
    def set_chart_data(self, chart_data: Dict, display_settings: Optional[Dict] = None):
        self._chart_data = chart_data
        self._is_transit_mode = False
        if display_settings:
            self._settings.update(display_settings)
        self._rebuild()

    def set_transit_chart_data(self, natal_chart: Dict, transit_planets: List[Dict],
                               transit_aspects: List[Dict],
                               display_settings: Optional[Dict] = None):
        self._chart_data = natal_chart
        self._transit_planets = transit_planets or []
        self._transit_aspects = transit_aspects or []
        self._is_transit_mode = True
        if display_settings:
            self._settings.update(display_settings)
        self._rebuild()

    def set_svg(self, svg_content: str):
        """Только для экспорта. Если данных нет — покажет баннер-диагноз."""
        self._svg_content = svg_content
        if self._chart_data is None:
            self._scene = QGraphicsScene(self)
            self.setScene(self._scene)
            item = self._scene.addText(
                "ДИАГНОЗ: получен только SVG, данные карты не переданы.\n"
                "main_window.py должен вызывать set_chart_data(...).\n"
                "Проверьте замену методов _update_chart_view / "
                "_update_transit_chart_view.")
            item.setDefaultTextColor(QColor("#C0392B"))
            self._scene.setSceneRect(self._scene.itemsBoundingRect())

    def set_transit_data(self, transit_planets, transit_aspects):
        self._transit_planets = transit_planets or []
        self._transit_aspects = transit_aspects or []

    def set_show_transits(self, show: bool):
        pass  # переключение выполняет MainWindow пересборкой сцены

    # ------------------------------------------------------------ сборка
    def _rebuild(self):
        if not self._chart_data:
            return
        self._scene = QGraphicsScene(0, 0, SCENE_SIZE, SCENE_SIZE, self)
        self.setScene(self._scene)
        self._scene.addRect(0, 0, SCENE_SIZE, SCENE_SIZE,
                            QPen(Qt.PenStyle.NoPen), QBrush(QColor("white")))
        if self._is_transit_mode:
            self._build_transit()
        else:
            self._build_natal()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_factor = 1.0

    def _pen(self, color, width, dash=False):
        pen = QPen(QColor(color), width)
        if dash:
            pen.setStyle(Qt.PenStyle.DashLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        return pen

    def _text(self, x, y, s, size, color, bold=True, symbol=False):
        item = QGraphicsSimpleTextItem(s)
        font = QFont("Segoe UI Symbol" if symbol else "Segoe UI", size)
        font.setBold(bold)
        item.setFont(font)
        item.setBrush(QBrush(QColor(color)))
        r = item.boundingRect()
        item.setPos(x - r.width() / 2, y - r.height() / 2)
        self._scene.addItem(item)
        return item

    def _glyph(self, name, x, y, box, color):
        """Рисует векторный глиф объекта с центром в (x, y)."""
        g = get_glyph(name)
        if g is None:
            return
        path, fills = g
        k = box / 100.0
        tr = QTransform().translate(x - box / 2, y - box / 2).scale(k, k)
        item = self._scene.addPath(tr.map(path), self._pen(color, GLYPH_STROKE * k))
        item.setZValue(5)
        for rect in fills:
            f = self._scene.addEllipse(tr.mapRect(rect), QPen(Qt.PenStyle.NoPen),
                                       QBrush(QColor(color)))
            f.setZValue(5)

    def _show_label(self, name):
        s = self._settings
        if name == "Chiron":
            return s["show_asteroid_labels"]
        if name in ("MeanNode", "TrueNode", "SouthNode"):
            return s["show_node_labels"]
        return s["show_planet_labels"]

    def _color(self, name, palette):
        override = self._settings.get(palette, {}) or {}
        return QColor(override.get(name, (PLANET_COLORS if palette == "planet_colors"
                                          else ASPECT_COLORS).get(name, "#000000")))

    def _place_planets(self, planets, radius, dot_r, glyph_box, label_offset):
        """Точки + векторные глифы. Возвращает словарь позиций для аспектов."""
        c = SCENE_SIZE / 2
        positions = {}
        used = []
        for pl in sorted(planets, key=lambda p: p.get("longitude", 0)):
            lon = pl.get("longitude")
            if lon is None:
                continue
            name = pl.get("name", "?")
            r = radius
            shifts = 0
            for ulon, _ in used:
                if shifts >= 3:
                    break
                if _angular_diff(lon, ulon) < 5.0:
                    cand = r - SCENE_SIZE * 0.025
                    if cand >= SCENE_SIZE * 0.25:
                        r, shifts = cand, shifts + 1
            used.append((lon, r))

            pos = lon_to_point(lon, r, c)
            positions[name] = pos
            color = self._color(name, "planet_colors")
            retro = pl.get("retrograde", False)
            dot_pen = self._pen("#D62828", 2.0) if retro else self._pen("#FFFFFF", 1.0)
            dot = self._scene.addEllipse(QRectF(pos.x() - dot_r, pos.y() - dot_r,
                                                2 * dot_r, 2 * dot_r),
                                         dot_pen, QBrush(color))
            dot.setZValue(4)

            if self._show_label(name):
                lp = lon_to_point(lon, r + label_offset, c)
                mode = self._settings["label_mode"]
                if mode != "words":
                    self._glyph(name, lp.x(), lp.y(), glyph_box, color.name())
                if mode != "symbols":
                    self._text(lp.x(), lp.y() + glyph_box,
                               name, 11, color.name())
        return positions

    def _draw_zodiac(self, r_in, r_out, font_size):
        c = SCENE_SIZE / 2
        for i, sign in enumerate(SIGNS):
            b = i * 30.0
            p1, p2 = lon_to_point(b, r_in, c), lon_to_point(b, r_out, c)
            self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), self._pen("#3a3a3a", 1.0))
            mp = lon_to_point(b + 15.0, (r_in + r_out) / 2, c)
            self._text(mp.x(), mp.y(), SIGN_SYMBOLS[sign], font_size, "#1a1a1a",
                       symbol=True)

    def _draw_houses(self, houses, r_in, r_out):
        if not houses or not self._settings["show_houses"]:
            return
        c = SCENE_SIZE / 2
        for h in houses:
            lon = h.get("longitude")
            if lon is None:
                continue
            n = h.get("house", 0)
            p1, p2 = lon_to_point(lon, r_in, c), lon_to_point(lon, r_out, c)
            w = 1.8 if n == 1 else 1.0
            self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), self._pen("#2a2a2a", w))
            nxt = houses[n % len(houses)].get("longitude", lon)
            mid = (lon + ((nxt - lon) % 360) / 2) % 360
            mp = lon_to_point(mid, (r_in + r_out) / 2, c)
            self._text(mp.x(), mp.y(), str(n), 11, "#4a4a4a")

    def _draw_angles(self, points, r_from, r_to):
        if not self._settings["show_angle_labels"]:
            return
        c = SCENE_SIZE / 2
        for pt in points:
            name, lon = pt.get("name"), pt.get("longitude")
            if name not in ("ASC", "MC") or lon is None:
                continue
            color = "#E74C3C" if name == "ASC" else "#3498DB"
            p1, p2 = lon_to_point(lon, r_from, c), lon_to_point(lon, r_to, c)
            self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), self._pen(color, 2.5))
            tp = lon_to_point(lon, r_to + SCENE_SIZE * 0.04, c)
            self._text(tp.x(), tp.y(), name, 16, color)

    def _draw_aspects(self, aspects, positions, dash=False, opacity=0.7):
        if not self._settings["show_aspects"]:
            return
        for a in aspects:
            pa, pb = a.get("point_a"), a.get("point_b")
            if pa in positions and pb in positions:
                pen = self._pen(self._color(a.get("aspect", ""), "aspect_colors"),
                                1.0, dash)
                line = self._scene.addLine(positions[pa].x(), positions[pa].y(),
                                           positions[pb].x(), positions[pb].y(), pen)
                line.setOpacity(opacity)

    def _build_natal(self):
        c = SCENE_SIZE / 2
        s = SCENE_SIZE
        self._scene.addEllipse(QRectF(0, 0, 0, 0)) if False else None
        for r, col, w, dash in ((s * R_OUTER, "#1a1a1a", 2.5, False),
                                (s * R_ZODIAC, "#2a2a2a", 1.5, False),
                                (s * R_HOUSES, "#4a4a4a", 0.8, True),
                                (s * R_ASPECTS, "#6a6a6a", 0.6, True)):
            d = 2 * r
            self._scene.addEllipse(QRectF(c - r, c - r, d, d), self._pen(col, w, dash))
        self._draw_zodiac(s * R_ZODIAC, s * R_OUTER, 20)
        self._draw_houses(self._chart_data.get("houses", []), s * R_ASPECTS, s * R_HOUSES)
        positions = self._place_planets(self._chart_data.get("planets", []),
                                        s * R_PLANETS,
                                        self._settings["planet_dot_size"],
                                        30, s * 0.045)
        self._draw_angles(self._chart_data.get("additional_points", []),
                          s * R_HOUSES, s * R_OUTER)
        self._draw_aspects(self._chart_data.get("aspects", []), positions)

    def _build_transit(self):
        c = SCENE_SIZE / 2
        s = SCENE_SIZE
        r_tr, r_nat, r_asp = s * 0.360, s * 0.280, s * 0.240
        for r, col, w, dash in ((s * R_OUTER, "#000000", 2.0, False),
                                (s * R_ZODIAC, "#000000", 1.0, False),
                                (r_tr, "#000000", 0.6, True),
                                (r_nat, "#000000", 0.6, False),
                                (r_asp, "#888888", 0.6, True)):
            d = 2 * r
            self._scene.addEllipse(QRectF(c - r, c - r, d, d), self._pen(col, w, dash))
        self._draw_zodiac(s * R_ZODIAC, s * R_OUTER, 18)
        self._draw_houses(self._chart_data.get("houses", []), r_asp, r_nat)
        nat_pos = self._place_planets(self._chart_data.get("planets", []),
                                      r_nat, 5, 24, s * 0.03)
        tr_pos = self._place_planets(self._transit_planets, r_tr, 5, 24, s * 0.03)
        self._draw_aspects(self._chart_data.get("aspects", []), nat_pos, opacity=0.6)
        for a in self._transit_aspects:
            tp, np_ = a.get("transit_planet"), a.get("natal_point")
            if tp in tr_pos and np_ in nat_pos:
                pen = self._pen(self._color(a.get("aspect", ""), "aspect_colors"),
                                1.0, True)
                line = self._scene.addLine(tr_pos[tp].x(), tr_pos[tp].y(),
                                           nat_pos[np_].x(), nat_pos[np_].y(), pen)
                line.setOpacity(0.8)
        self._draw_angles(self._chart_data.get("additional_points", []), r_nat, s * R_OUTER)

    # ------------------------------------------------------------ UX
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            super().wheelEvent(event)

    def zoom_in(self, factor=1.2):
        if self._zoom_factor * factor <= self._max_zoom:
            self.scale(factor, factor)
            self._zoom_factor *= factor

    def zoom_out(self, factor=1.2):
        if self._zoom_factor / factor >= self._min_zoom:
            self.scale(1 / factor, 1 / factor)
            self._zoom_factor /= factor

    def reset_view(self):
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_factor = 1.0

    def set_zoom(self, zoom: float):
        zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        self.scale(zoom / self._zoom_factor, zoom / self._zoom_factor)
        self._zoom_factor = zoom

    def get_zoom(self) -> float:
        return self._zoom_factor

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.chart_clicked.emit(self.mapToScene(event.pos()))
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_0:
            self.reset_view()
        elif event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._zoom_factor == 1.0 and self._scene.sceneRect().isValid():
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    # ------------------------------------------------------------ экспорт
    def save_svg(self, file_path: str) -> bool:
        if not self._svg_content:
            return False
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self._svg_content)
            return True
        except Exception:
            return False

    def render_to_image(self, width: int, height: int) -> QImage:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor("white"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._scene.render(painter)
        painter.end()
        return image