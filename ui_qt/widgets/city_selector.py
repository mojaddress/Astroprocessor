"""
City Selector - Widget for selecting cities with timezone support.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QLabel, QCompleter, QStringListModel
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional

from astro_core.controllers import CityController
from astro_core.controllers.city_controller import City


class CitySelector(QWidget):
    """Widget for selecting a city with autocomplete."""
    
    # Signals
    city_selected = pyqtSignal(object)  # City
    
    def __init__(self, city_controller: CityController, label: str = "Город", parent=None):
        super().__init__(parent)
        self._city_controller = city_controller
        self._selected_city: Optional[City] = None
        
        self._init_ui(label)
        
    def _init_ui(self, label: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Label
        if label:
            lbl = QLabel(label)
            layout.addWidget(lbl)
            
        # Search input
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Введите название города...")
        layout.addWidget(self.edit_search)
        
        # Completer for autocomplete
        self._completer = QCompleter(self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.edit_search.setCompleter(self._completer)
        
        # Combo box for selection
        self.combo_cities = QComboBox()
        self.combo_cities.setEnabled(False)
        layout.addWidget(self.combo_cities)
        
        # Info label
        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.lbl_info)
        
        # Connect
        self.edit_search.textChanged.connect(self._on_search_changed)
        self.combo_cities.currentIndexChanged.connect(self._on_city_selected)
        
    def _on_search_changed(self, text: str):
        """Update completer and combo with search results."""
        if text.strip():
            cities = self._city_controller.search_cities(text, limit=20)
        else:
            cities = self._city_controller.get_all_cities()[:20]
            
        # Update completer
        display_names = [self._city_controller.get_city_display_name(c) for c in cities]
        model = QStringListModel(display_names, self)
        self._completer.setModel(model)
        
        # Update combo
        self.combo_cities.blockSignals(True)
        self.combo_cities.clear()
        for name in display_names:
            self.combo_cities.addItem(name)
        self.combo_cities.setEnabled(len(cities) > 0)
        self.combo_cities.blockSignals(False)
        
    def _on_city_selected(self, index: int):
        """Handle city selection."""
        if index < 0:
            self._selected_city = None
            self.city_selected.emit(None)
            return
            
        city_name = self.combo_cities.currentText()
        city = self._city_controller.get_city_by_name(city_name)
        if city:
            self._selected_city = city
            self.lbl_info.setText(
                f"🏙️ {city.name}, {city.country} · "
                f"{city.latitude:.2f}, {city.longitude:.2f} · "
                f"TZ: {city.timezone}"
            )
            self.city_selected.emit(city)
        else:
            self._selected_city = None
            self.city_selected.emit(None)
            
    def get_selected_city(self) -> Optional[City]:
        return self._selected_city
        
    def set_city(self, city: City):
        """Set selected city programmatically."""
        self._selected_city = city
        display_name = self._city_controller.get_city_display_name(city)
        self.edit_search.setText(display_name)
        self.combo_cities.setCurrentText(display_name)
        self.lbl_info.setText(
            f"🏙️ {city.name}, {city.country} · "
            f"{city.latitude:.2f}, {city.longitude:.2f} · "
            f"TZ: {city.timezone}"
        )