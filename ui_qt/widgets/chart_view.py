"""
Chart View - SVG rendering with QGraphicsView for interactive charts.
Supports zoom (mouse wheel), pan (drag), and reset.
Uses QSvgRenderer + QGraphicsPixmapItem with proper text rendering.
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QByteArray
from PyQt6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent, QPixmap, QPainter
from typing import List, Dict, Optional


class ChartView(QGraphicsView):
    """Interactive chart view with zoom and pan support."""
    
    # Signals
    chart_clicked = pyqtSignal(QPointF)  # Scene coordinates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Pixmap item for rendered SVG
        self._pixmap_item = None
        self._renderer = None
        self._svg_content = ""
        
        # Transit data
        self._transit_planets: List[Dict] = []
        self._transit_aspects: List[Dict] = []
        self._show_transits = True
        
        # View settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
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
        """Set SVG content to display by rendering to pixmap with proper text rendering."""
        self._scene.clear()
        self._svg_content = svg_content
        
        # Create renderer from SVG string
        svg_bytes = svg_content.encode('utf-8')
        self._renderer = QSvgRenderer(QByteArray(svg_bytes))
        
        if not self._renderer.isValid():
            return
            
        # Render SVG to pixmap with proper text rendering
        pixmap = self._render_svg_to_pixmap()
        if pixmap.isNull():
            return
            
        # Create pixmap item
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(self._pixmap_item)
        
        # Set scene rect to SVG bounds
        self._scene.setSceneRect(self._renderer.viewBoxF())
        
        # Fit to view initially
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_factor = 1.0
        
    def _render_svg_to_pixmap(self) -> QPixmap:
        """Render SVG to pixmap using QSvgRenderer with proper text rendering."""
        # Get SVG size from renderer
        view_box = self._renderer.viewBoxF()
        if view_box.isEmpty():
            return QPixmap()
            
        # Create pixmap with the SVG's intrinsic size
        size = view_box.size().toSize()
        # Ensure minimum size
        if size.width() < 100:
            size.setWidth(800)
        if size.height() < 100:
            size.setHeight(800)
            
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Render SVG to pixmap with text antialiasing
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._renderer.render(painter)
        painter.end()
        
        return pixmap
        
    def get_svg_item(self):
        """Get the SVG graphics item (returns pixmap item)."""
        return self._pixmap_item
    
    def set_transit_data(self, transit_planets: List[Dict], transit_aspects: List[Dict]):
        """Set transit data for display."""
        self._transit_planets = transit_planets or []
        self._transit_aspects = transit_aspects or []
    
    def set_show_transits(self, show: bool):
        """Toggle transit display."""
        self._show_transits = show
        # Note: Actual transit display requires re-rendering SVG with/without transits
        # This is handled by MainWindow which re-renders the chart
    
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
        if self._pixmap_item:
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
        if self._svg_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._svg_content)
                return True
            except Exception:
                return False
        return False
        
    def render_to_image(self, width: int, height: int):
        """Render current view to QImage."""
        from PyQt6.QtGui import QImage
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        self.render(painter)
        painter.end()
        return image