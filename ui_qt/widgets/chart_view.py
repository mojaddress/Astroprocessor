"""
Chart View — векторный виджет карты (финальная версия итерации 26).
"""
import math
from typing import Dict, List, Optional

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsSimpleTextItem
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (QWheelEvent, QMouseEvent, QKeyEvent, QPainter, QPen,
                         QBrush, QColor, QFont, QTransform, QImage, QPainterPath)

from .astro_glyphs import get_glyph, GLYPH_STROKE
from astro_core.constants import get_planet_name_ru, get_sign_name_ru
from astro_core.interpretations import aspect_tooltip

SCENE_SIZE = 800
R_OUTER, R_ZODIAC = 0.440, 0.405
R_HOUSES, R_PLANETS, R_ASPECTS = 0.370, 0.325, 0.295

SIGN_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}
SIGN_NAMES_RU = {
    "Aries": "Овен", "Taurus": "Телец", "Gemini": "Близнецы", "Cancer": "Рак",
    "Leo": "Лев", "Virgo": "Дева", "Libra": "Весы", "Scorpio": "Скорпион",
    "Sagittarius": "Стрелец", "Capricorn": "Козерог", "Aquarius": "Водолей",
    "Pisces": "Рыбы",
}
SIGN_EXTRA = {
    "Aries": ("огонь", "Марс"), "Taurus": ("земля", "Венера"),
    "Gemini": ("воздух", "Меркурий"), "Cancer": ("вода", "Луна"),
    "Leo": ("огонь", "Солнце"), "Virgo": ("земля", "Меркурий"),
    "Libra": ("воздух", "Венера"), "Scorpio": ("вода", "Плутон/Марс"),
    "Sagittarius": ("огонь", "Юпитер"), "Capricorn": ("земля", "Сатурн"),
    "Aquarius": ("воздух", "Сатурн/Уран"), "Pisces": ("вода", "Юпитер/Нептун"),
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
ASPECT_NAMES_RU = {
    "conjunction": "Соединение", "sextile": "Секстиль", "square": "Квадрат",
    "trine": "Тригон", "opposition": "Оппозиция",
}


def lon_to_point(lon, radius, c):
    a = math.radians(180.0 - lon)
    return QPointF(c + radius * math.cos(a), c - radius * math.sin(a))


def _angular_diff(a, b):
    d = abs(a - b) % 360.0
    return 360.0 - d if d > 180.0 else d


class ChartView(QGraphicsView):
    chart_clicked = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._chart_data = None
        self._chart_b = None
        self._transit_planets = []
        self._transit_aspects = []
        self._synastry_aspects = []
        self._is_transit_mode = False
        self._is_synastry_mode = False
        self._svg_content = ""
        self._settings = {
            "show_planet_labels": True, "show_sign_names": False,
            "show_houses": True, "show_aspects": True, "show_legend": True,
            "show_angle_labels": True, "show_dsc": True,
            "text_chiron": True, "text_nodes": True, "text_fortune": True,
            "label_mode": "symbols",
            "planet_colors": {}, "aspect_colors": {}, "planet_dot_size": 6,
        }
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._zoom_factor = 1.0
        self._min_zoom, self._max_zoom = 0.1, 20.0

    def set_chart_data(self, chart_data, display_settings=None):
        self._chart_data = chart_data
        self._is_transit_mode = False
        self._is_synastry_mode = False
        if display_settings:
            self._settings.update(display_settings)
        self._rebuild()

    def set_transit_chart_data(self, natal_chart, transit_planets, transit_aspects,
                               display_settings=None):
        self._chart_data = natal_chart
        self._transit_planets = transit_planets or []
        self._transit_aspects = transit_aspects or []
        self._is_transit_mode = True
        self._is_synastry_mode = False
        if display_settings:
            self._settings.update(display_settings)
        self._rebuild()

    def set_synastry_chart_data(self, chart_a, chart_b, synastry_aspects,
                                display_settings=None):
        self._chart_data = chart_a
        self._chart_b = chart_b
        self._synastry_aspects = synastry_aspects or []
        self._is_transit_mode = False
        self._is_synastry_mode = True
        if display_settings:
            self._settings.update(display_settings)
        self._rebuild()

    def set_svg(self, svg_content):
        self._svg_content = svg_content
        if self._chart_data is None:
            self._scene = QGraphicsScene(self)
            self.setScene(self._scene)
            item = self._scene.addText(
                "ДИАГНОЗ: получен только SVG, данные карты не переданы.")
            item.setDefaultTextColor(QColor("#C0392B"))
            self._scene.setSceneRect(self._scene.itemsBoundingRect())

    def set_transit_data(self, transit_planets, transit_aspects):
        self._transit_planets = transit_planets or []
        self._transit_aspects = transit_aspects or []

    def set_show_transits(self, show):
        pass

    def _rebuild(self):
        if not self._chart_data:
            return
        self._scene = QGraphicsScene(0, 0, SCENE_SIZE, SCENE_SIZE, self)
        self.setScene(self._scene)
        self._scene.addRect(0, 0, SCENE_SIZE, SCENE_SIZE,
                            QPen(Qt.PenStyle.NoPen), QBrush(QColor("white")))
        if self._is_synastry_mode:
            self._build_synastry()
        elif self._is_transit_mode:
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

    def _text_left(self, x, y, s, size, color, bold=False):
        item = QGraphicsSimpleTextItem(s)
        font = QFont("Segoe UI", size)
        font.setBold(bold)
        item.setFont(font)
        item.setBrush(QBrush(QColor(color)))
        r = item.boundingRect()
        item.setPos(x, y - r.height() / 2)
        self._scene.addItem(item)
        return item

    def _glyph(self, name, x, y, box, color, tooltip=None):
        g = get_glyph(name)
        if g is None:
            return
        path, fills = g
        k = box / 100.0
        tr = QTransform().translate(x - box / 2, y - box / 2).scale(k, k)
        item = self._scene.addPath(tr.map(path), self._pen(color, GLYPH_STROKE * k))
        item.setZValue(5)
        if tooltip:
            item.setToolTip(tooltip)
        for rect in fills:
            f = self._scene.addEllipse(tr.mapRect(rect), QPen(Qt.PenStyle.NoPen),
                                       QBrush(QColor(color)))
            f.setZValue(5)
            if tooltip:
                f.setToolTip(tooltip)

    def _text_label(self, name):
        s = self._settings
        if name == "Chiron":
            return bool(s.get("text_chiron", False))
        if name in ("MeanNode", "TrueNode", "SouthNode"):
            return bool(s.get("text_nodes", False))
        if name == "PartOfFortune":
            return bool(s.get("text_fortune", False))
        return bool(s.get("show_planet_labels", False))

    def _color(self, name, palette):
        override = self._settings.get(palette, {}) or {}
        base = PLANET_COLORS if palette == "planet_colors" else ASPECT_COLORS
        return QColor(override.get(name, base.get(name, "#000000")))

    def _format_tooltip(self, pl):
        name = pl.get("name", "?")
        lines = [get_planet_name_ru(name)]
        lon = pl.get("longitude")
        deg = pl.get("degree_in_sign")
        if deg is None and lon is not None:
            deg = lon % 30.0
        if deg is not None:
            d = int(deg)
            m = int(round((deg - d) * 60))
            if m == 60:
                d, m = d + 1, 0
            sign_ru = get_sign_name_ru(pl.get("sign", "")) if pl.get("sign") else ""
            lines.append(f"{d:02d}°{m:02d}' {sign_ru}".rstrip())
        if pl.get("house"):
            lines.append(f"Дом: {pl.get('house')}")
        if pl.get("retrograde"):
            lines.append("Ретроградная")
        if pl.get("speed_longitude") is not None:
            lines.append(f"Скорость: {pl['speed_longitude']:+.2f}°/день")
        return "\n".join(lines)

    def _place_planets(self, planets, radius, dot_r, glyph_box, label_offset):
        c = SCENE_SIZE / 2
        positions = {}
        used_dots = []
        for pl in sorted(planets, key=lambda p: p.get("longitude", 0)):
            lon = pl.get("longitude")
            if lon is None:
                continue
            name = pl.get("name", "?")
            r = radius
            shifts = 0
            for ulon, _ in used_dots:
                if shifts >= 2:
                    break
                if _angular_diff(lon, ulon) < 3.0:
                    cand = r - SCENE_SIZE * 0.015
                    if cand >= SCENE_SIZE * 0.25:
                        r, shifts = cand, shifts + 1
            used_dots.append((lon, r))
            positions[name] = (lon_to_point(lon, r, c), pl, r)

        used_labels = []
        for name, (pos, pl, dot_radius) in positions.items():
            lon = pl.get("longitude")
            color = self._color(name, "planet_colors")
            tip = self._format_tooltip(pl)
            dot_pen = self._pen("#D62828", 2.0) if pl.get("retrograde") else self._pen("#FFFFFF", 1.0)
            dot = self._scene.addEllipse(QRectF(pos.x() - dot_r, pos.y() - dot_r,
                                                2 * dot_r, 2 * dot_r), dot_pen, QBrush(color))
            dot.setZValue(4)
            dot.setToolTip(tip)
            dot.setAcceptHoverEvents(True)
            label_radius = dot_radius + label_offset
            for attempt in range(5):
                tp = lon_to_point(lon, label_radius + attempt * glyph_box * 0.4, c)
                if all(math.hypot(tp.x() - up.x(), tp.y() - up.y()) >= glyph_box * 1.2
                       for _ul, up in used_labels):
                    used_labels.append((lon, tp))
                    mode = self._settings["label_mode"]
                    if mode != "words":
                        self._glyph(name, tp.x(), tp.y(), glyph_box, color.name(), tooltip=tip)
                    if pl.get("retrograde"):
                        self._text(tp.x() + glyph_box * 0.45, tp.y() - glyph_box * 0.45,
                                   "R", 9, "#D62828")
                    if mode != "symbols" or self._text_label(name):
                        self._text(tp.x(), tp.y() + glyph_box,
                                   get_planet_name_ru(name), 10, color.name())
                    break
        return {n: d[0] for n, d in positions.items()}

    def _sign_periods_by_sign(self, year):
        cache = getattr(self, "_sign_periods_cache", None)
        if cache is None:
            cache = self._sign_periods_cache = {}
        if year in cache:
            return cache[year]
        try:
            from astro_core.zodiac_calendar import sign_periods
            by_sign = {}
            for sign, s, e in sign_periods(year):
                by_sign.setdefault(sign, []).append((s, e))
        except Exception:
            by_sign = {}
        cache[year] = by_sign
        return by_sign

    def _sign_tooltip(self, sign, year, periods):
        el, ru = SIGN_EXTRA.get(sign, ("—", "—"))
        lines = [f"{SIGN_NAMES_RU[sign]} ({SIGN_SYMBOLS[sign]})",
                 f"Стихия: {el}; управитель: {ru}"]
        segs = periods.get(sign, [])
        if segs:
            txt = "; ".join(f"{s.strftime('%d.%m')} – {e.strftime('%d.%m')}"
                            for s, e in segs)
            lines.append(f"Солнце в знаке в {year}: {txt}")
        return "\n".join(lines)

    def _draw_zodiac(self, r_in, r_out, font_size):
        c = SCENE_SIZE / 2
        try:
            year = int(str((self._chart_data or {}).get("birth", {}).get("date", ""))[:4])
        except Exception:
            year = 0
        if not year:
            from datetime import date as _date
            year = _date.today().year
        periods = self._sign_periods_by_sign(year)
        for i, sign in enumerate(SIGNS):
            b = i * 30.0
            p1, p2 = lon_to_point(b, r_in, c), lon_to_point(b, r_out, c)
            self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), self._pen("#3a3a3a", 1.0))
            mid_r = (r_in + r_out) / 2
            tip = self._sign_tooltip(sign, year, periods)
            if self._settings.get("show_sign_names", False):
                sp = lon_to_point(b + 15.0, mid_r + 9, c)
                t1 = self._text(sp.x(), sp.y(), SIGN_SYMBOLS[sign], font_size - 2,
                                "#1a1a1a", symbol=True)
                np_ = lon_to_point(b + 15.0, mid_r - 9, c)
                t2 = self._text(np_.x(), np_.y(), SIGN_NAMES_RU[sign], 8, "#444444")
                t1.setToolTip(tip)
                t2.setToolTip(tip)
            else:
                mp = lon_to_point(b + 15.0, mid_r, c)
                t1 = self._text(mp.x(), mp.y(), SIGN_SYMBOLS[sign], font_size,
                                "#1a1a1a", symbol=True)
                t1.setToolTip(tip)
            path = QPainterPath()
            outer = [lon_to_point(b + t, r_out, c) for t in range(0, 31, 3)]
            inner = [lon_to_point(b + t, r_in, c) for t in range(30, -1, -3)]
            path.moveTo(outer[0])
            for pt in outer[1:]:
                path.lineTo(pt)
            for pt in inner:
                path.lineTo(pt)
            path.closeSubpath()
            item = self._scene.addPath(path, QPen(Qt.PenStyle.NoPen),
                                       QBrush(QColor(0, 0, 0, 0)))
            item.setToolTip(tip)
            item.setZValue(1)
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
            if name not in ("ASC", "MC", "DSC") or lon is None:
                continue
            if name == "DSC" and not self._settings.get("show_dsc", True):
                continue
            color = {"ASC": "#E74C3C", "MC": "#3498DB",
                     "DSC": "#16A085"}.get(name, "#888888")
            p1, p2 = lon_to_point(lon, r_from, c), lon_to_point(lon, r_to, c)
            self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), self._pen(color, 2.5))
            tp = lon_to_point(lon, r_to + SCENE_SIZE * 0.04, c)
            self._text(tp.x(), tp.y(), name, 16, color)

    def _add_aspect_line(self, p1, p2, aspect, color, width, dash=False,
                         opacity=0.7, tooltip=""):
        if aspect == "conjunction":
            c = SCENE_SIZE / 2
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            ctrl = QPointF(mid.x() + (c - mid.x()) * 0.35, mid.y() + (c - mid.y()) * 0.35)
            path = QPainterPath(p1)
            path.quadTo(ctrl, p2)
            item = self._scene.addPath(path, self._pen(color, width, dash))
        else:
            item = self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(),
                                       self._pen(color, width, dash))
        if tooltip:
            item.setToolTip(tooltip)
        item.setOpacity(opacity)
        return item

    def _draw_aspects(self, aspects, positions, dash=False, opacity=0.7):
        if not self._settings["show_aspects"]:
            return
        for a in aspects:
            pa, pb = a.get("point_a"), a.get("point_b")
            if pa in positions and pb in positions:
                self._add_aspect_line(positions[pa], positions[pb], a.get("aspect", ""),
                                      self._color(a.get("aspect", ""), "aspect_colors"),
                                      1.0, dash, opacity,
                                      aspect_tooltip(a.get("aspect", ""), pa, pb))

    def _draw_point_of_fortune(self, additional, radius, dot_r, glyph_box):
        c = SCENE_SIZE / 2
        for pt in additional:
            if pt.get("name") != "PartOfFortune":
                continue
            lon = pt.get("longitude")
            if lon is None:
                continue
            pos = lon_to_point(lon, radius, c)
            color = QColor("#B8860B")
            tip = self._format_tooltip(pt)
            dot = self._scene.addEllipse(QRectF(pos.x() - dot_r, pos.y() - dot_r,
                                                2 * dot_r, 2 * dot_r),
                                         self._pen("#FFFFFF", 1.0), QBrush(color))
            dot.setZValue(4)
            dot.setToolTip(tip)
            dot.setAcceptHoverEvents(True)
            lp = lon_to_point(lon, radius + glyph_box * 0.8, c)
            self._glyph("PartOfFortune", lp.x(), lp.y(), glyph_box, color.name(), tooltip=tip)
            if self._text_label("PartOfFortune"):
                self._text(lp.x(), lp.y() + glyph_box, "Фортуна", 10, color.name())
            return pos
        return None

    def _draw_legend(self):
        if not self._settings.get("show_legend", True):
            return
        items = list(ASPECT_NAMES_RU.items())
        y0 = SCENE_SIZE - 26.0 - 16.0 * len(items)
        for i, (key, ru) in enumerate(items):
            y = y0 + i * 16.0
            self._scene.addLine(26.0, y, 48.0, y,
                                self._pen(self._color(key, "aspect_colors"), 2.0))
            self._text_left(56.0, y, ru, 10, "#333333")

    def _draw_title(self, title, color="#1a1a1a"):
        self._text(SCENE_SIZE / 2, SCENE_SIZE * 0.0125, title, 16, color, bold=True)

    def _build_natal(self):
        c = SCENE_SIZE / 2
        s = SCENE_SIZE
        self._draw_title(f"Натальная карта: {self._chart_data.get('birth', {}).get('name', 'Карта')}")
        for r, col, w, dash in ((s * R_OUTER, "#1a1a1a", 2.5, False),
                                (s * R_ZODIAC, "#2a2a2a", 1.5, False),
                                (s * R_HOUSES, "#4a4a4a", 0.8, True),
                                (s * R_ASPECTS, "#6a6a6a", 0.6, True)):
            self._scene.addEllipse(QRectF(c - r, c - r, 2 * r, 2 * r), self._pen(col, w, dash))
        self._draw_zodiac(s * R_ZODIAC, s * R_OUTER, 17)
        self._draw_houses(self._chart_data.get("houses", []), s * R_ASPECTS, s * R_HOUSES)
        positions = self._place_planets(self._chart_data.get("planets", []),
                                        s * R_PLANETS, self._settings["planet_dot_size"],
                                        30, s * 0.028)
        self._draw_angles(self._chart_data.get("additional_points", []),
                          s * R_HOUSES, s * R_OUTER)
        pof = self._draw_point_of_fortune(self._chart_data.get("additional_points", []),
                                          s * R_PLANETS, self._settings["planet_dot_size"], 26)
        if pof is not None:
            positions["PartOfFortune"] = pof
        self._draw_aspects(self._chart_data.get("aspects", []), positions)
        self._draw_legend()

    def _build_transit(self):
        c = SCENE_SIZE / 2
        s = SCENE_SIZE
        r_tr, r_nat, r_asp = s * 0.360, s * 0.280, s * 0.240
        self._draw_title(f"Транзитная карта: {self._chart_data.get('birth', {}).get('name', 'Карта')}")
        for r, col, w, dash in ((s * R_OUTER, "#000000", 2.0, False),
                                (s * R_ZODIAC, "#000000", 1.0, False),
                                (r_tr, "#000000", 0.6, True),
                                (r_nat, "#000000", 0.6, False),
                                (r_asp, "#888888", 0.6, True)):
            self._scene.addEllipse(QRectF(c - r, c - r, 2 * r, 2 * r), self._pen(col, w, dash))
        self._draw_zodiac(s * R_ZODIAC, s * R_OUTER, 15)
        self._draw_houses(self._chart_data.get("houses", []), r_asp, r_nat)
        nat_pos = self._place_planets(self._chart_data.get("planets", []), r_nat, 5, 24, s * 0.02)
        tr_pos = self._place_planets(self._transit_planets, r_tr, 5, 24, s * 0.02)
        pof = self._draw_point_of_fortune(self._chart_data.get("additional_points", []), r_nat, 5, 22)
        if pof is not None:
            nat_pos["PartOfFortune"] = pof
        self._draw_aspects(self._chart_data.get("aspects", []), nat_pos, opacity=0.6)
        for a in self._transit_aspects:
            tp, np_ = a.get("transit_planet"), a.get("natal_point")
            if tp in tr_pos and np_ in nat_pos:
                self._add_aspect_line(tr_pos[tp], nat_pos[np_], a.get("aspect", ""),
                                      self._color(a.get("aspect", ""), "aspect_colors"),
                                      1.0, True, 0.8,
                                      aspect_tooltip(a.get("aspect", ""), tp, np_))
        self._draw_angles(self._chart_data.get("additional_points", []), r_nat, s * R_OUTER)
        self._draw_legend()

    def _build_synastry(self):
        c = SCENE_SIZE / 2
        s = SCENE_SIZE
        r_tr, r_nat = s * 0.360, s * 0.280
        na = self._chart_data.get("birth", {}).get("name", "A")
        nb = (self._chart_b or {}).get("birth", {}).get("name", "B")
        self._draw_title(f"Синастрия: {na} + {nb}")
        for r, col, w, dash in ((s * R_OUTER, "#000000", 2.0, False),
                                (s * R_ZODIAC, "#000000", 1.0, False),
                                (r_tr, "#000000", 0.6, True),
                                (r_nat, "#000000", 0.6, False),
                                (s * R_ASPECTS, "#888888", 0.6, True)):
            self._scene.addEllipse(QRectF(c - r, c - r, 2 * r, 2 * r), self._pen(col, w, dash))
        self._draw_zodiac(s * R_ZODIAC, s * R_OUTER, 15)
        pa = self._place_planets(self._chart_data.get("planets", []), r_nat, 5, 24, s * 0.02)
        pb = self._place_planets((self._chart_b or {}).get("planets", []), r_tr, 5, 24, s * 0.02)
        for a in self._synastry_aspects:
            p1n, p2n = a.get("point_a"), a.get("point_b")
            if a.get("point_a_chart") == "A":
                p1, p2 = pa.get(p1n), pb.get(p2n)
            else:
                p1, p2 = pb.get(p1n), pa.get(p2n)
            if p1 is None or p2 is None:
                continue
            self._add_aspect_line(p1, p2, a.get("aspect", ""),
                                  self._color(a.get("aspect", ""), "aspect_colors"),
                                  1.2, False, 0.85,
                                  aspect_tooltip(a.get("aspect", ""), p1n, p2n))
        self._draw_legend()

    def wheelEvent(self, event):
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

    def set_zoom(self, zoom):
        zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        self.scale(zoom / self._zoom_factor, zoom / self._zoom_factor)
        self._zoom_factor = zoom

    def get_zoom(self):
        return self._zoom_factor

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.chart_clicked.emit(self.mapToScene(event.pos()))
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
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

    def save_svg(self, file_path):
        if not self._svg_content:
            return False
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self._svg_content)
            return True
        except Exception:
            return False

    def render_to_image(self, width, height):
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor("white"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._scene.render(painter)
        painter.end()
        return image
