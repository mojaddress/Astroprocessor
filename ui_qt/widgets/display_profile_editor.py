"""
Display Profile Editor - Widget for customizing display profiles.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QDoubleSpinBox, QColorDialog, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTabWidget, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPalette
from typing import List, Dict, Any

from astro_core.controllers import DisplayProfileController
from astro_core.display_profiles import ALL_PLANETS, ALL_ASPECTS, DEFAULT_ORBS
from astro_core.chart_svg import PLANET_COLORS, ASPECT_COLORS
from astro_core.constants import get_planet_name_ru, get_aspect_name_ru


class ColorButton(QPushButton):
    """Button that shows and selects a color."""
    
    color_changed = pyqtSignal(str)
    
    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(32, 24)
        self.clicked.connect(self._pick_color)
        self._update_style()
        
    def _update_style(self):
        self.setStyleSheet(
            f"background-color: {self._color.name()}; border: 1px solid #888;"
        )
        
    def _pick_color(self):
        color = QColorDialog.getColor(self._color, self, "Выберите цвет")
        if color.isValid():
            self._color = color
            self._update_style()
            self.color_changed.emit(color.name())
            
    def get_color(self) -> str:
        return self._color.name()
        
    def set_color(self, color: str):
        self._color = QColor(color)
        self._update_style()


class DisplayProfileEditor(QWidget):
    """Widget for editing display profiles."""
    
    # Signals
    profile_applied = pyqtSignal(str)
    profile_saved = pyqtSignal(str, dict)  # name, profile_data
    profile_deleted = pyqtSignal(str)
    
    def __init__(self, display_profile_controller: DisplayProfileController, parent=None):
        super().__init__(parent)
        self._controller = display_profile_controller
        self._current_profile_name = "full"
        
        self._init_ui()
        self._load_profiles()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Profile selector
        selector_group = QGroupBox("Профиль отображения")
        selector_layout = QVBoxLayout(selector_group)
        
        self.combo_profiles = QComboBox()
        selector_layout.addWidget(self.combo_profiles)
        
        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton("📥 Применить")
        self.btn_save = QPushButton("💾 Сохранить как...")
        self.btn_delete = QPushButton("🗑️ Удалить")
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        selector_layout.addLayout(btn_layout)
        
        self.edit_new_name = QLineEdit()
        self.edit_new_name.setPlaceholderText("Имя для нового профиля")
        selector_layout.addWidget(self.edit_new_name)
        
        layout.addWidget(selector_group)
        
        # Editor tabs
        self.tabs = QTabWidget()
        
        # Objects tab
        self.tab_objects = self._create_objects_tab()
        self.tabs.addTab(self.tab_objects, "Объекты")
        
        # Aspects tab
        self.tab_aspects = self._create_aspects_tab()
        self.tabs.addTab(self.tab_aspects, "Аспекты")
        
        # Appearance tab
        self.tab_appearance = self._create_appearance_tab()
        self.tabs.addTab(self.tab_appearance, "Внешний вид")
        
        layout.addWidget(self.tabs)
        
        # Connect
        self.btn_apply.clicked.connect(
            lambda: self.profile_applied.emit(self.combo_profiles.currentText())
        )
        self.btn_save.clicked.connect(self._on_save)
        self.btn_delete.clicked.connect(self._on_delete)
        self.combo_profiles.currentTextChanged.connect(self._on_profile_changed)
        
    def _create_objects_tab(self) -> QWidget:
        """Create objects configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Planets
        planets_group = QGroupBox("Планеты")
        planets_layout = QVBoxLayout(planets_group)
        
        self.planet_checkboxes = {}
        for planet in ALL_PLANETS:
            chk = QCheckBox(get_planet_name_ru(planet))
            chk.setChecked(True)
            chk.setProperty("planet", planet)
            self.planet_checkboxes[planet] = chk
            planets_layout.addWidget(chk)
            
        layout.addWidget(planets_group)
        
        # Special objects
        special_group = QGroupBox("Специальные объекты")
        special_layout = QVBoxLayout(special_group)
        
        self.chk_chiron = QCheckBox("Хирон")
        self.chk_chiron.setChecked(True)
        self.chk_nodes = QCheckBox("Лунные узлы (Раху/Кету)")
        self.chk_nodes.setChecked(True)
        self.chk_fortune = QCheckBox("Part of Fortune (Парс Фортуны)")
        self.chk_fortune.setChecked(True)
        self.chk_angles = QCheckBox("ASC / MC (Углы)")
        self.chk_angles.setChecked(True)
        
        special_layout.addWidget(self.chk_chiron)
        special_layout.addWidget(self.chk_nodes)
        special_layout.addWidget(self.chk_fortune)
        special_layout.addWidget(self.chk_angles)
        
        layout.addWidget(special_group)
        layout.addStretch()
        
        return widget
        
    def _create_aspects_tab(self) -> QWidget:
        """Create aspects configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Aspects table
        self.table_aspects = QTableWidget()
        self.table_aspects.setColumnCount(3)
        self.table_aspects.setHorizontalHeaderLabels(["Аспект", "Включить", "Орб (°)"])
        self.table_aspects.horizontalHeader().setStretchLastSection(True)
        self.table_aspects.setAlternatingRowColors(True)
        
        self.aspect_checkboxes = {}
        self.aspect_orbs = {}
        
        for i, aspect in enumerate(ALL_ASPECTS):
            self.table_aspects.insertRow(i)
            
            # Name
            name_item = QTableWidgetItem(get_aspect_name_ru(aspect))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_aspects.setItem(i, 0, name_item)
            
            # Enabled checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            chk.setProperty("aspect", aspect)
            self.aspect_checkboxes[aspect] = chk
            self.table_aspects.setCellWidget(i, 1, chk)
            
            # Orb spinbox
            spin = QDoubleSpinBox()
            spin.setRange(0, 30)
            spin.setDecimals(1)
            spin.setSingleStep(0.5)
            spin.setValue(DEFAULT_ORBS[aspect])
            spin.setProperty("aspect", aspect)
            self.aspect_orbs[aspect] = spin
            self.table_aspects.setCellWidget(i, 2, spin)
            
        layout.addWidget(self.table_aspects)
        
        return widget
        
    def _create_appearance_tab(self) -> QWidget:
        """Create appearance configuration tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Label mode
        label_group = QGroupBox("Режим подписей")
        label_layout = QHBoxLayout(label_group)
        
        self.radio_symbols = QRadioButton("Символы")
        self.radio_words = QRadioButton("Слова")
        self.radio_both = QRadioButton("Символы + слова")
        self.radio_symbols.setChecked(True)
        
        label_btn_group = QButtonGroup(self)
        label_btn_group.addButton(self.radio_symbols)
        label_btn_group.addButton(self.radio_words)
        label_btn_group.addButton(self.radio_both)
        
        label_layout.addWidget(self.radio_symbols)
        label_layout.addWidget(self.radio_words)
        label_layout.addWidget(self.radio_both)
        layout.addWidget(label_group)
        
        # Show options
        show_group = QGroupBox("Отображать")
        show_layout = QHBoxLayout(show_group)
        
        self.chk_show_aspects = QCheckBox("Линии аспектов")
        self.chk_show_aspects.setChecked(True)
        self.chk_show_houses = QCheckBox("Номера домов")
        self.chk_show_houses.setChecked(True)
        
        show_layout.addWidget(self.chk_show_aspects)
        show_layout.addWidget(self.chk_show_houses)
        layout.addWidget(show_group)
        
        # Sizes
        size_group = QGroupBox("Размеры")
        size_layout = QFormLayout(size_group)
        
        self.spin_chart_size = QSpinBox()
        self.spin_chart_size.setRange(400, 2000)
        self.spin_chart_size.setSingleStep(100)
        self.spin_chart_size.setValue(800)
        size_layout.addRow("Размер карты:", self.spin_chart_size)
        
        self.spin_dot_size = QSpinBox()
        self.spin_dot_size.setRange(2, 15)
        self.spin_dot_size.setValue(5)
        size_layout.addRow("Размер точек планет:", self.spin_dot_size)
        
        layout.addWidget(size_group)
        
        # Planet colors
        colors_group = QGroupBox("Цвета планет")
        colors_layout = QVBoxLayout(colors_group)
        
        self.planet_color_buttons = {}
        for planet in ALL_PLANETS:
            row = QHBoxLayout()
            label = QLabel(get_planet_name_ru(planet))
            label.setMinimumWidth(120)
            btn = ColorButton(PLANET_COLORS.get(planet, "#000000"))
            btn.color_changed.connect(lambda c, p=planet: self._on_planet_color_changed(p, c))
            self.planet_color_buttons[planet] = btn
            row.addWidget(label)
            row.addWidget(btn)
            row.addStretch()
            colors_layout.addLayout(row)
            
        layout.addWidget(colors_group)
        
        # Aspect colors
        aspect_colors_group = QGroupBox("Цвета аспектов")
        aspect_colors_layout = QVBoxLayout(aspect_colors_group)
        
        self.aspect_color_buttons = {}
        for aspect in ALL_ASPECTS:
            row = QHBoxLayout()
            label = QLabel(get_aspect_name_ru(aspect))
            label.setMinimumWidth(120)
            btn = ColorButton(ASPECT_COLORS.get(aspect, "#888888"))
            btn.color_changed.connect(lambda c, a=aspect: self._on_aspect_color_changed(a, c))
            self.aspect_color_buttons[aspect] = btn
            row.addWidget(label)
            row.addWidget(btn)
            row.addStretch()
            aspect_colors_layout.addLayout(row)
            
        layout.addWidget(aspect_colors_group)
        
        scroll.setWidget(widget)
        return scroll
        
    def _on_planet_color_changed(self, planet: str, color: str):
        pass  # Handled by color button signal
        
    def _on_aspect_color_changed(self, aspect: str, color: str):
        pass  # Handled by color button signal
        
    def _load_profiles(self):
        """Load profiles into combo."""
        self.combo_profiles.clear()
        profiles = self._controller.list_profiles()
        for p in profiles:
            self.combo_profiles.addItem(p.name)
            
        # Select current
        index = self.combo_profiles.findText(self._current_profile_name)
        if index >= 0:
            self.combo_profiles.setCurrentIndex(index)
            
    def _on_profile_changed(self, name: str):
        """Load profile data into editor."""
        self._current_profile_name = name
        try:
            profile = self._controller.load_profile(name)
            self._populate_from_profile(profile)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить профиль: {e}")
            
    def _populate_from_profile(self, profile):
        """Fill editor with profile data."""
        data = self._controller._profile_to_dict(profile)
        
        # Objects
        objects = data.get("objects", {})
        for planet, chk in self.planet_checkboxes.items():
            chk.setChecked(objects.get(planet, True))
        self.chk_chiron.setChecked(objects.get("Chiron", True))
        self.chk_nodes.setChecked(objects.get("LunarNodes", True))
        self.chk_fortune.setChecked(objects.get("PartOfFortune", True))
        self.chk_angles.setChecked(objects.get("Angles", True))
        
        # Aspects
        aspects = data.get("aspects", {})
        for aspect, chk in self.aspect_checkboxes.items():
            chk.setChecked(aspects.get(aspect, {}).get("enabled", True))
        for aspect, spin in self.aspect_orbs.items():
            spin.setValue(aspects.get(aspect, {}).get("orb", DEFAULT_ORBS[aspect]))
            
        # Appearance
        appearance = data.get("appearance", {})
        label_mode = appearance.get("label_mode", "symbols")
        if label_mode == "symbols":
            self.radio_symbols.setChecked(True)
        elif label_mode == "words":
            self.radio_words.setChecked(True)
        else:
            self.radio_both.setChecked(True)
            
        self.chk_show_aspects.setChecked(appearance.get("show_aspect_lines", True))
        self.chk_show_houses.setChecked(appearance.get("show_houses", True))
        self.spin_chart_size.setValue(appearance.get("chart_size", 800))
        self.spin_dot_size.setValue(appearance.get("planet_dot_size", 5))
        
        planet_colors = appearance.get("planet_colors", {})
        for planet, btn in self.planet_color_buttons.items():
            btn.set_color(planet_colors.get(planet, PLANET_COLORS.get(planet, "#000000")))
            
        aspect_colors = appearance.get("aspect_colors", {})
        for aspect, btn in self.aspect_color_buttons.items():
            btn.set_color(aspect_colors.get(aspect, ASPECT_COLORS.get(aspect, "#888888")))
            
    def _collect_profile_data(self) -> dict:
        """Collect current editor state into profile dict."""
        # Objects
        objects = {}
        for planet, chk in self.planet_checkboxes.items():
            objects[planet] = chk.isChecked()
        objects["Chiron"] = self.chk_chiron.isChecked()
        objects["LunarNodes"] = self.chk_nodes.isChecked()
        objects["PartOfFortune"] = self.chk_fortune.isChecked()
        objects["Angles"] = self.chk_angles.isChecked()
        
        # Aspects
        aspects = {}
        for aspect in ALL_ASPECTS:
            aspects[aspect] = {
                "enabled": self.aspect_checkboxes[aspect].isChecked(),
                "orb": self.aspect_orbs[aspect].value(),
            }
            
        # Appearance
        label_mode = "symbols"
        if self.radio_words.isChecked():
            label_mode = "words"
        elif self.radio_both.isChecked():
            label_mode = "both"
            
        planet_colors = {}
        for planet, btn in self.planet_color_buttons.items():
            planet_colors[planet] = btn.get_color()
            
        aspect_colors = {}
        for aspect, btn in self.aspect_color_buttons.items():
            aspect_colors[aspect] = btn.get_color()
            
        appearance = {
            "label_mode": label_mode,
            "show_houses": self.chk_show_houses.isChecked(),
            "show_aspect_lines": self.chk_show_aspects.isChecked(),
            "chart_size": self.spin_chart_size.value(),
            "planet_dot_size": self.spin_dot_size.value(),
            "planet_colors": planet_colors,
            "aspect_colors": aspect_colors,
        }
        
        return {
            "name": self.edit_new_name.text().strip() or self._current_profile_name,
            "description": "Пользовательский профиль отображения",
            "objects": objects,
            "aspects": aspects,
            "appearance": appearance,
        }
        
    def _on_save(self):
        """Save current editor state as new profile."""
        name = self.edit_new_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя профиля")
            return
            
        profile_data = self._collect_profile_data()
        profile_data["name"] = name
        
        # Validate
        errors = self._controller.validate_profile(
            self._controller._dict_to_profile(profile_data)
        )
        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return
            
        self.profile_saved.emit(name, profile_data)
        self.edit_new_name.clear()
        
    def _on_delete(self):
        """Delete current profile."""
        name = self.combo_profiles.currentText()
        if name in ["classic", "vedic", "minimal", "full"]:
            QMessageBox.warning(self, "Ошибка", "Встроенные профили нельзя удалить")
            return
            
        reply = QMessageBox.question(
            self, "Удалить профиль",
            f"Удалить профиль '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_deleted.emit(name)