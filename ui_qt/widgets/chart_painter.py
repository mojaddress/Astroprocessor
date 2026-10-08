"""
Chart Painter - прямая отрисовка астрологических карт через QPainter.

Решает проблему с отображением символов планет, которую не решает QSvgRenderer.
Рисует карту напрямую на QPainter, что гарантирует:
- Чёткие линии на любом разрешении
- Правильное отображение символов планет
- Поддержку HiDPI дисплеев
- Высокое качество рендеринга
"""

import math
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap


# ============================================================
# Константы отрисовки
# ============================================================

# Цвета аспектов
ASPECT_COLORS = {
    "conjunction": QColor("#FF4500"),
    "sextile": QColor("#1E90FF"),
    "square": QColor("#DC143C"),
    "trine": QColor("#228B22"),
    "opposition": QColor("#8A2BE2"),
}

# Цвета планет
PLANET_COLORS = {
    "Sun": QColor("#FF8C00"),
    "Moon": QColor("#808080"),
    "Mercury": QColor("#DAA520"),
    "Venus": QColor("#32CD32"),
    "Mars": QColor("#FF4500"),
    "Jupiter": QColor("#9932CC"),
    "Saturn": QColor("#1C1C1C"),
    "Uranus": QColor("#00BFFF"),
    "Neptune": QColor("#008B8B"),
    "Pluto": QColor("#8B0000"),
    "MeanNode": QColor("#696969"),
    "TrueNode": QColor("#696969"),
    "SouthNode": QColor("#A9A9A9"),
    "Chiron": QColor("#8B4513"),
}

# Символы планет
PLANET_SYMBOLS = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
    "MeanNode": "☊",
    "TrueNode": "☊",
    "SouthNode": "☋",
    "Chiron": "⚷",
}

# Символы знаков зодиака
SIGN_SYMBOLS = {
    "Aries": "♈",
    "Taurus": "♉",
    "Gemini": "♊",
    "Cancer": "♋",
    "Leo": "♌",
    "Virgo": "♍",
    "Libra": "♎",
    "Scorpio": "♏",
    "Sagittarius": "♐",
    "Capricorn": "♑",
    "Aquarius": "♒",
    "Pisces": "♓",
}

SIGN_NAMES_RU = {
    "Aries": "Овен",
    "Taurus": "Телец",
    "Gemini": "Близнецы",
    "Cancer": "Рак",
    "Leo": "Лев",
    "Virgo": "Дева",
    "Libra": "Весы",
    "Scorpio": "Скорпион",
    "Sagittarius": "Стрелец",
    "Capricorn": "Козерог",
    "Aquarius": "Водолей",
    "Pisces": "Рыбы",
}

SIGNS = list(SIGN_SYMBOLS.keys())

# Радиусы колец (доля от размера)
R_OUTER = 0.440
R_ZODIAC = 0.405
R_HOUSES = 0.370
R_PLANETS = 0.325
R_ASPECTS = 0.295


def longitude_to_point(longitude: float, radius: float, cx: float, cy: float) -> QPointF:
    """Преобразует астрологическую долготу в координаты на плоскости."""
    angle_deg = 180.0 - longitude
    angle_rad = math.radians(angle_deg)
    x = cx + radius * math.cos(angle_rad)
    y = cy - radius * math.sin(angle_rad)
    return QPointF(x, y)


def get_planet_font(size: int = 18) -> QFont:
    """Возвращает шрифт для символов планет с приоритетом для астрономических символов."""
    # Список шрифтов в порядке приоритета
    font_families = [
        "Segoe UI Symbol",
        "Arial Unicode MS",
        "DejaVu Sans",
        "Noto Sans Symbols",
        "Noto Sans Symbols 2",
        "Symbola",
        "FreeSerif",
        "Arial",
        "sans-serif",
    ]
    
    font = QFont()
    font.setPointSize(size)
    font.setBold(True)
    
    # Устанавливаем список шрифтов
    font.setFamilies(font_families)
    
    return font


def get_sign_font(size: int = 14) -> QFont:
    """Возвращает шрифт для символов знаков зодиака."""
    return get_planet_font(size)


def get_text_font(size: int = 10) -> QFont:
    """Возвращает обычный шрифт для текста."""
    font = QFont("Segoe UI", size)
    font.setBold(False)
    return font


class ChartPainter:
    """Отрисовщик астрологических карт через QPainter."""
    
    def __init__(self, size: int = 800):
        self.size = size
        self.cx = size / 2
        self.cy = size / 2
        
        # Радиусы
        self.r_outer = size * R_OUTER
        self.r_zodiac = size * R_ZODIAC
        self.r_houses = size * R_HOUSES
        self.r_planets = size * R_PLANETS
        self.r_aspects = size * R_ASPECTS
        
        # Настройки
        self.show_planet_labels = True
        self.show_asteroid_labels = True
        self.show_node_labels = True
        self.show_angle_labels = True
        self.show_houses = True
        self.show_aspects = True
        self.label_mode = "symbols"  # "symbols", "words", "both"
        
    def render_to_pixmap(self, chart_data: Dict, device_pixel_ratio: float = 1.0) -> QPixmap:
        """Отрисовывает натальную карту в QPixmap."""
        # Создаём pixmap с учётом HiDPI
        pixmap_size = int(self.size * device_pixel_ratio)
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.GlobalColor.white)
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        
        # Создаём painter
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Масштабируем под размер
        painter.scale(device_pixel_ratio, device_pixel_ratio)
        
        # Отрисовываем
        self._draw_chart(painter, chart_data)
        
        painter.end()
        return pixmap
    
    def render_transit_to_pixmap(
        self,
        natal_chart: Dict,
        transit_planets: List[Dict],
        transit_aspects: List[Dict],
        device_pixel_ratio: float = 1.0
    ) -> QPixmap:
        """Отрисовывает транзитную карту в QPixmap."""
        pixmap_size = int(self.size * device_pixel_ratio)
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.GlobalColor.white)
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        painter.scale(device_pixel_ratio, device_pixel_ratio)
        
        self._draw_transit_chart(painter, natal_chart, transit_planets, transit_aspects)
        
        painter.end()
        return pixmap
    
    def _draw_chart(self, painter: QPainter, chart_data: Dict):
        """Основная отрисовка натальной карты."""
        # 1. Круги
        self._draw_circles(painter)
        
        # 2. Знаки зодиака
        self._draw_zodiac_signs(painter)
        
        # 3. Дома
        if self.show_houses:
            self._draw_houses(painter, chart_data.get("houses", []))
        
        # 4. Планеты
        planet_positions = self._draw_planets(painter, chart_data.get("planets", []))
        
        # 5. ASC и MC
        self._draw_angles(painter, chart_data.get("additional_points", []))
        
        # 6. Аспекты
        if self.show_aspects:
            self._draw_aspects(painter, chart_data.get("aspects", []), planet_positions)
    
    def _draw_circles(self, painter: QPainter):
        """Рисует основные круги карты."""
        pen = QPen(QColor("#1a1a1a"), 2.5)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(self.cx, self.cy), self.r_outer, self.r_outer)
        
        pen = QPen(QColor("#2a2a2a"), 1.5)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(self.cx, self.cy), self.r_zodiac, self.r_zodiac)
        
        pen = QPen(QColor("#4a4a4a"), 0.8)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(self.cx, self.cy), self.r_houses, self.r_houses)
        
        pen = QPen(QColor("#6a6a6a"), 0.6)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(self.cx, self.cy), self.r_aspects, self.r_aspects)
    
    def _draw_zodiac_signs(self, painter: QPainter):
        """Рисует знаки зодиака."""
        font = get_sign_font(16)
        painter.setFont(font)
        
        for i, sign in enumerate(SIGNS):
            # Граница знака
            boundary_lon = i * 30.0
            p1 = longitude_to_point(boundary_lon, self.r_zodiac, self.cx, self.cy)
            p2 = longitude_to_point(boundary_lon, self.r_outer, self.cx, self.cy)
            
            pen = QPen(QColor("#3a3a3a"), 1.0)
            painter.setPen(pen)
            painter.drawLine(p1, p2)
            
            # Символ знака
            mid_lon = boundary_lon + 15.0
            text_pos = longitude_to_point(mid_lon, (self.r_zodiac + self.r_outer) / 2, self.cx, self.cy)
            
            symbol = SIGN_SYMBOLS.get(sign, "")
            painter.setPen(QColor("#1a1a1a"))
            self._draw_centered_text(painter, text_pos, symbol)
    
    def _draw_houses(self, painter: QPainter, houses: List[Dict]):
        """Рисует дома."""
        if not houses:
            return
        
        font = get_text_font(11)
        painter.setFont(font)
        
        for house in houses:
            cusp_lon = house.get("longitude")
            if cusp_lon is None:
                continue
            
            p1 = longitude_to_point(cusp_lon, self.r_aspects, self.cx, self.cy)
            p2 = longitude_to_point(cusp_lon, self.r_houses, self.cx, self.cy)
            
            house_num = house.get("house", 0)
            line_width = 1.8 if house_num == 1 else 1.0
            
            pen = QPen(QColor("#2a2a2a"), line_width)
            painter.setPen(pen)
            painter.drawLine(p1, p2)
            
            # Номер дома
            next_idx = house_num % len(houses)
            next_cusp_lon = houses[next_idx].get("longitude", cusp_lon)
            diff = (next_cusp_lon - cusp_lon) % 360
            mid_lon = (cusp_lon + diff / 2) % 360
            
            text_pos = longitude_to_point(mid_lon, (self.r_aspects + self.r_houses) / 2, self.cx, self.cy)
            painter.setPen(QColor("#4a4a4a"))
            self._draw_centered_text(painter, text_pos, str(house_num))
    
    def _draw_planets(self, painter: QPainter, planets: List[Dict]) -> Dict[str, QPointF]:
        """Рисует планеты и их символы. Возвращает позиции для аспектов."""
        planet_positions = {}
        sorted_planets = sorted(planets, key=lambda p: p.get("longitude", 0))
        
        # Группируем планеты по долготе для умного смещения
        used_positions = []
        
        for planet in sorted_planets:
            lon = planet.get("longitude")
            if lon is None:
                continue
            
            planet_name = planet.get("name", "?")
            
            # Умное смещение при наложении
            radius = self._resolve_planet_radius(lon, used_positions)
            used_positions.append((lon, radius))
            
            pos = longitude_to_point(lon, radius, self.cx, self.cy)
            planet_positions[planet_name] = pos
            
            # Цвет планеты
            color = PLANET_COLORS.get(planet_name, QColor("#000000"))
            is_retrograde = planet.get("retrograde", False)
            
            # Точка планеты
            dot_size = 6
            painter.setBrush(QBrush(color))
            if is_retrograde:
                painter.setPen(QPen(QColor("#D62828"), 2.0))
            else:
                painter.setPen(QPen(QColor("#ffffff"), 1.0))
            
            painter.drawEllipse(pos, dot_size, dot_size)
            
            # Символ планеты
            should_show = self._should_show_label(planet_name)
            if should_show:
                symbol = PLANET_SYMBOLS.get(planet_name, "?")
                
                # Позиция символа (немного дальше от центра)
                label_pos = longitude_to_point(lon, radius + self.size * 0.04, self.cx, self.cy)
                
                # Цвет текста
                text_color = color
                if color.lightness() < 50:  # Тёмные цвета делаем чёрными
                    text_color = QColor("#000000")
                
                painter.setPen(text_color)
                font = get_planet_font(18)
                painter.setFont(font)
                self._draw_centered_text(painter, label_pos, symbol)
        
        return planet_positions
    
    def _draw_angles(self, painter: QPainter, additional_points: List[Dict]):
        """Рисует ASC и MC."""
        for point in additional_points:
            point_name = point.get("name")
            lon = point.get("longitude")
            
            if point_name is None or lon is None:
                continue
            
            if not self.show_angle_labels:
                continue
            
            if point_name == "ASC":
                p1 = longitude_to_point(lon, self.r_houses, self.cx, self.cy)
                p2 = longitude_to_point(lon, self.r_outer, self.cx, self.cy)
                
                pen = QPen(QColor("#E74C3C"), 2.5)
                painter.setPen(pen)
                painter.drawLine(p1, p2)
                
                # Подпись
                text_pos = longitude_to_point(lon, self.r_outer + self.size * 0.04, self.cx, self.cy)
                painter.setPen(QColor("#E74C3C"))
                font = get_text_font(14)
                font.setBold(True)
                painter.setFont(font)
                self._draw_centered_text(painter, text_pos, "ASC")
            
            elif point_name == "MC":
                p1 = longitude_to_point(lon, self.r_houses, self.cx, self.cy)
                p2 = longitude_to_point(lon, self.r_outer, self.cx, self.cy)
                
                pen = QPen(QColor("#3498DB"), 2.5)
                painter.setPen(pen)
                painter.drawLine(p1, p2)
                
                # Подпись
                text_pos = longitude_to_point(lon, self.r_outer + self.size * 0.04, self.cx, self.cy)
                painter.setPen(QColor("#3498DB"))
                font = get_text_font(14)
                font.setBold(True)
                painter.setFont(font)
                self._draw_centered_text(painter, text_pos, "MC")
    
    def _draw_aspects(self, painter: QPainter, aspects: List[Dict], planet_positions: Dict[str, QPointF]):
        """Рисует аспекты между планетами."""
        for aspect in aspects:
            point_a = aspect.get("point_a")
            point_b = aspect.get("point_b")
            aspect_name = aspect.get("aspect")
            
            if point_a in planet_positions and point_b in planet_positions:
                pos_a = planet_positions[point_a]
                pos_b = planet_positions[point_b]
                
                color = ASPECT_COLORS.get(aspect_name, QColor("#888888"))
                pen = QPen(color, 0.8)
                pen.setStyle(Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.setOpacity(0.7)
                painter.drawLine(pos_a, pos_b)
                painter.setOpacity(1.0)
    
    def _draw_transit_chart(self, painter: QPainter, natal_chart: Dict,
                            transit_planets: List[Dict], transit_aspects: List[Dict]):
        """Отрисовка транзитной карты."""
        # Радиусы для транзитной карты
        r_outer = self.size * 0.440
        r_zodiac = self.size * 0.405
        r_transit = self.size * 0.360
        r_natal = self.size * 0.280
        r_aspects = self.size * 0.240
        
        # Круги
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawEllipse(QPointF(self.cx, self.cy), r_outer, r_outer)
        
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.drawEllipse(QPointF(self.cx, self.cy), r_zodiac, r_zodiac)
        
        pen = QPen(QColor("#000000"), 0.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(self.cx, self.cy), r_transit, r_transit)
        
        painter.setPen(QPen(QColor("#000000"), 0.5))
        painter.drawEllipse(QPointF(self.cx, self.cy), r_natal, r_natal)
        
        pen = QPen(QColor("#888888"), 0.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(self.cx, self.cy), r_aspects, r_aspects)
        
        # Знаки зодиака
        font = get_sign_font(14)
        painter.setFont(font)
        
        for i, sign in enumerate(SIGNS):
            boundary_lon = i * 30.0
            p1 = longitude_to_point(boundary_lon, r_zodiac, self.cx, self.cy)
            p2 = longitude_to_point(boundary_lon, r_outer, self.cx, self.cy)
            
            painter.setPen(QPen(QColor("#000000"), 0.8))
            painter.drawLine(p1, p2)
            
            mid_lon = boundary_lon + 15.0
            text_pos = longitude_to_point(mid_lon, (r_zodiac + r_outer) / 2, self.cx, self.cy)
            symbol = SIGN_SYMBOLS.get(sign, "")
            painter.setPen(QColor("#000000"))
            self._draw_centered_text(painter, text_pos, symbol)
        
        # Натальные планеты
        natal_planets = natal_chart.get("planets", [])
        natal_positions = self._draw_planets_at_radius(painter, natal_planets, r_natal)
        
        # Транзитные планеты
        transit_positions = self._draw_planets_at_radius(painter, transit_planets, r_transit)
        
        # Натальные аспекты
        self._draw_aspects(painter, natal_chart.get("aspects", []), natal_positions)
        
        # Транзитные аспекты
        for aspect in transit_aspects:
            transit_name = aspect.get("transit_planet")
            natal_name = aspect.get("natal_point")
            aspect_name = aspect.get("aspect")
            
            if transit_name in transit_positions and natal_name in natal_positions:
                pos_a = transit_positions[transit_name]
                pos_b = natal_positions[natal_name]
                
                color = ASPECT_COLORS.get(aspect_name, QColor("#888888"))
                pen = QPen(color, 1.0)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setOpacity(0.8)
                painter.drawLine(pos_a, pos_b)
                painter.setOpacity(1.0)
    
    def _draw_planets_at_radius(self, painter: QPainter, planets: List[Dict], radius: float) -> Dict[str, QPointF]:
        """Рисует планеты на заданном радиусе."""
        positions = {}
        sorted_planets = sorted(planets, key=lambda p: p.get("longitude", 0))
        used_positions = []
        
        for planet in sorted_planets:
            lon = planet.get("longitude")
            if lon is None:
                continue
            
            planet_name = planet.get("name", "?")
            
            # Умное смещение
            adjusted_radius = self._resolve_planet_radius(lon, used_positions, radius)
            used_positions.append((lon, adjusted_radius))
            
            pos = longitude_to_point(lon, adjusted_radius, self.cx, self.cy)
            positions[planet_name] = pos
            
            color = PLANET_COLORS.get(planet_name, QColor("#000000"))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#ffffff"), 1.0))
            painter.drawEllipse(pos, 5, 5)
            
            # Символ
            if self._should_show_label(planet_name):
                symbol = PLANET_SYMBOLS.get(planet_name, "?")
                label_pos = longitude_to_point(lon, adjusted_radius + self.size * 0.025, self.cx, self.cy)
                
                text_color = color if color.lightness() > 50 else QColor("#000000")
                painter.setPen(text_color)
                font = get_planet_font(16)
                painter.setFont(font)
                self._draw_centered_text(painter, label_pos, symbol)
        
        return positions
    
    def _should_show_label(self, planet_name: str) -> bool:
        """Определяет, показывать ли подпись для объекта."""
        if planet_name in ["Chiron"]:
            return self.show_asteroid_labels
        elif planet_name in ["MeanNode", "TrueNode", "SouthNode"]:
            return self.show_node_labels
        else:
            return self.show_planet_labels
    
    def _resolve_planet_radius(self, lon: float, used_positions: List[Tuple[float, float]],
                                base_radius: Optional[float] = None) -> float:
        """Умное смещение планеты при наложении."""
        if base_radius is None:
            base_radius = self.r_planets
        
        radius = base_radius
        min_radius = self.size * 0.25
        max_shifts = 3
        shift_step = self.size * 0.025
        proximity_deg = 5.0
        
        shifts = 0
        for used_lon, _ in used_positions:
            if shifts >= max_shifts:
                break
            
            diff = abs(lon - used_lon) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff
            
            if diff < proximity_deg:
                candidate = radius - shift_step
                if candidate >= min_radius:
                    radius = candidate
                    shifts += 1
        
        return radius
    
    def _draw_centered_text(self, painter: QPainter, pos: QPointF, text: str):
        """Рисует текст с центрированием в точке."""
        font_metrics = QFontMetrics(painter.font())
        text_width = font_metrics.horizontalAdvance(text)
        text_height = font_metrics.height()
        
        # Смещаем для центрирования
        x = pos.x() - text_width / 2
        y = pos.y() + text_height / 4
        
        painter.drawText(QPointF(x, y), text)