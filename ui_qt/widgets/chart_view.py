"""
Chart View - интерактивный виджет для отображения астрологических карт.

Использует ChartPainter для прямой отрисовки через QPainter.
Поддерживает:
- Зум (колесо мыши + Ctrl)
- Панорамирование (перетаскивание)
- Сброс вида
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent, QPixmap, QPainter
from typing import List, Dict, Optional

from .chart_painter import ChartPainter


class ChartView(QGraphicsView):
    """Интерактивный виджет для отображения карт."""
    
    # Сигналы
    chart_clicked = pyqtSignal(QPointF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Отрисовщик
        self._painter = ChartPainter(size=800)
        
        # Текущие данные
        self._chart_data: Optional[Dict] = None
        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._svg_content = ""  # Для обратной совместимости
        
        # Транзиты
        self._transit_planets: List[Dict] = []
        self._transit_aspects: List[Dict] = []
        self._show_transits = True
        self._is_transit_mode = False
        
        # Настройки отображения
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Состояние зума
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 10.0
    
    def set_svg(self, svg_content: str):
        """Устанавливает SVG контент (для обратной совместимости)."""
        self._svg_content = svg_content
        # Теперь используем ChartPainter, но сохраняем SVG для экспорта
    
    def set_chart_data(self, chart_data: Dict, display_settings: Optional[Dict] = None):
        """Устанавливает данные натальной карты для отрисовки."""
        self._chart_data = chart_data
        self._is_transit_mode = False
        
        if display_settings:
            self._apply_display_settings(display_settings)
        
        self._render_chart()
    
    def set_transit_chart_data(self, natal_chart: Dict, transit_planets: List[Dict],
                                transit_aspects: List[Dict], display_settings: Optional[Dict] = None):
        """Устанавливает данные транзитной карты."""
        self._chart_data = natal_chart
        self._transit_planets = transit_planets
        self._transit_aspects = transit_aspects
        self._is_transit_mode = True
        
        if display_settings:
            self._apply_display_settings(display_settings)
        
        self._render_chart()
    
    def _apply_display_settings(self, settings: Dict):
        """Применяет настройки отображения."""
        self._painter.show_planet_labels = settings.get("show_planet_labels", True)
        self._painter.show_asteroid_labels = settings.get("show_asteroid_labels", True)
        self._painter.show_node_labels = settings.get("show_node_labels", True)
        self._painter.show_angle_labels = settings.get("show_angle_labels", True)
        self._painter.show_houses = settings.get("show_houses", True)
        self._painter.show_aspects = settings.get("show_aspects", True)
        self._painter.label_mode = settings.get("label_mode", "symbols")
    
    def _render_chart(self):
        """Отрисовывает карту в сцену."""
        if not self._chart_data:
            return
        
        # Получаем devicePixelRatio для HiDPI
        device_pixel_ratio = self.devicePixelRatioF()
        if device_pixel_ratio <= 0:
            device_pixel_ratio = 1.0
        
        # Отрисовываем
        if self._is_transit_mode:
            pixmap = self._painter.render_transit_to_pixmap(
                self._chart_data,
                self._transit_planets,
                self._transit_aspects,
                device_pixel_ratio
            )
        else:
            pixmap = self._painter.render_to_pixmap(
                self._chart_data,
                device_pixel_ratio
            )
        
        if pixmap.isNull():
            return
        
        # Очищаем сцену и добавляем новый pixmap
        self._scene.clear()
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(self._pixmap_item)
        
        # Устанавливаем размер сцены
        self._scene.setSceneRect(0, 0, self._painter.size, self._painter.size)
        
        # Подгоняем вид
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_factor = 1.0
    
    def set_transit_data(self, transit_planets: List[Dict], transit_aspects: List[Dict]):
        """Устанавливает данные транзитов (для обратной совместимости)."""
        self._transit_planets = transit_planets or []
        self._transit_aspects = transit_aspects or []
    
    def set_show_transits(self, show: bool):
        """Включает/выключает отображение транзитов."""
        self._show_transits = show
    
    def wheelEvent(self, event: QWheelEvent):
        """Обработка колеса мыши для зума."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)
    
    def zoom_in(self, factor: float = 1.2):
        """Увеличить масштаб."""
        new_zoom = self._zoom_factor * factor
        if new_zoom <= self._max_zoom:
            self.scale(factor, factor)
            self._zoom_factor = new_zoom
    
    def zoom_out(self, factor: float = 1.2):
        """Уменьшить масштаб."""
        new_zoom = self._zoom_factor / factor
        if new_zoom >= self._min_zoom:
            self.scale(1.0 / factor, 1.0 / factor)
            self._zoom_factor = new_zoom
    
    def reset_view(self):
        """Сбросить вид."""
        if self._pixmap_item:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom_factor = 1.0
    
    def set_zoom(self, zoom: float):
        """Установить абсолютный масштаб."""
        zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        factor = zoom / self._zoom_factor
        self.scale(factor, factor)
        self._zoom_factor = zoom
    
    def get_zoom(self) -> float:
        """Получить текущий масштаб."""
        return self._zoom_factor
    
    def mousePressEvent(self, event: QMouseEvent):
        """Обработка клика мыши."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.chart_clicked.emit(scene_pos)
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Обработка клавиш."""
        if event.key() == Qt.Key.Key_0:
            self.reset_view()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)
    
    def save_svg(self, file_path: str) -> bool:
        """Сохраняет SVG в файл (для обратной совместимости)."""
        if self._svg_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._svg_content)
                return True
            except Exception:
                return False
        return False
    
    def render_to_image(self, width: int, height: int):
        """Отрисовывает текущий вид в QImage."""
        from PyQt6.QtGui import QImage
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        self.render(painter)
        painter.end()
        return image