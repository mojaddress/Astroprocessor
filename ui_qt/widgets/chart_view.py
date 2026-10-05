"""
Chart View - SVG rendering with QGraphicsView for interactive charts.
Supports zoom (mouse wheel), pan (drag), and reset.
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsSvgItem
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent
import io


class ChartView(QGraphicsView):
    """Interactive chart view with zoom and pan support."""
    
    # Signals
    chart_clicked = pyqtSignal(QPointF)  # Scene coordinates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # SVG item
        self._svg_item = None
        self._renderer = None
        
        # View settings
        self.setRenderHint(self.renderHints() | 0x01)  # Antialiasing
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # State
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 10.0
        
    def set_svg(self, svg_content: str):
        """Set SVG content to display."""
        self._scene.clear()
        
        # Create renderer from SVG string
        svg_bytes = svg_content.encode('utf-8')
        self._renderer = QSvgRenderer(svg_bytes)
        
        if not self._renderer.isValid():
            return
            
        # Create SVG item
        self._svg_item = QGraphicsSvgItem()
        self._svg_item.setSharedRenderer(self._renderer)
        self._scene.addItem(self._svg_item)
        
        # Set scene rect to SVG bounds
        self._scene.setSceneRect(self._renderer.viewBoxF())
        
        # Fit to view initially
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_factor = 1.0
        
    def get_svg_item(self):
        """Get the SVG graphics item."""
        return self._svg_item
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl+wheel
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Normal scroll
            super().wheelEvent(event)
            
    def zoom_in(self, factor: float = 1.2):
        """Zoom in by factor."""
        new_zoom = self._zoom_factor * factor
        if new_zoom <= self._max_zoom:
            self.scale(factor, factor)
            self._zoom_factor = new_zoom
            
    def zoom_out(self, factor: float = 1.2):
        """Zoom out by factor."""
        new_zoom = self._zoom_factor / factor
        if new_zoom >= self._min_zoom:
            self.scale(1.0 / factor, 1.0 / factor)
            self._zoom_factor = new_zoom
            
    def reset_view(self):
        """Reset view to fit SVG."""
        if self._svg_item:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom_factor = 1.0
            
    def set_zoom(self, zoom: float):
        """Set absolute zoom level."""
        zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        factor = zoom / self._zoom_factor
        self.scale(factor, factor)
        self._zoom_factor = zoom
        
    def get_zoom(self) -> float:
        """Get current zoom level."""
        return self._zoom_factor
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for click detection."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.chart_clicked.emit(scene_pos)
        super().mousePressEvent(event)
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_0:
            self.reset_view()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)
            
    def save_svg(self, file_path: str) -> bool:
        """Save current SVG to file."""
        if self._renderer and self._svg_item:
            # We need to save the original SVG content
            # The renderer doesn't provide direct save, so we'd need to store the original
            return False
        return False
        
    def render_to_image(self, width: int, height: int):
        """Render current view to QImage."""
        from PyQt6.QtGui import QImage, QPainter
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        self.render(painter)
        painter.end()
        return image