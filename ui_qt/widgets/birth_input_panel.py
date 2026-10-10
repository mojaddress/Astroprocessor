"""
Birth Input Panel - Widget for entering birth data.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QDateEdit, QTimeEdit, QDoubleSpinBox, QComboBox,
    QRadioButton, QButtonGroup, QPushButton, QLabel, QCheckBox,
    QCompleter, QMessageBox, QToolButton
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QStringListModel
from datetime import date, time
from typing import Optional, List, Callable

from astro_core.controllers import CityController, ProfileController
from astro_core.controllers.city_controller import City


from PyQt6.QtWidgets import QGridLayout


class CityCompleter(QCompleter):
    """Custom completer for city search."""
    
    def __init__(self, city_controller: CityController, parent=None):
        super().__init__(parent)
        self._city_controller = city_controller
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self._update_model("")
        
    def _update_model(self, query: str):
        if query.strip():
            cities = self._city_controller.search_cities(query, limit=20)
        else:
            cities = self._city_controller.get_all_cities()[:20]
            
        display_names = [self._city_controller.get_city_display_name(c) for c in cities]
        model = QStringListModel(display_names, self)
        self.setModel(model)


class BirthInputPanel(QWidget):
    """Panel for entering birth data and selecting profiles."""
    
    # Signals
    calculate_requested = pyqtSignal(dict, dict, str)  # birth_data, settings, display_profile_name
    profile_load_requested = pyqtSignal(str)
    profile_save_requested = pyqtSignal(str)  # editing_name or None
    profile_edit_requested = pyqtSignal(str)
    profile_delete_requested = pyqtSignal(str)
    display_profile_apply_requested = pyqtSignal(str)
    display_profile_save_requested = pyqtSignal(str)
    recalc_triggered = pyqtSignal()
    
    def __init__(
        self,
        city_controller: CityController,
        profile_controller: ProfileController,
        parent=None
    ):
        super().__init__(parent)
        self._city_controller = city_controller
        self._profile_controller = profile_controller
        self._editing_profile_name: Optional[str] = None
        
        self._init_ui()
        self._load_profiles()
        self._load_display_profiles()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # --- Profiles Group ---
        profiles_group = QGroupBox("👤 Профили")
        profiles_layout = QVBoxLayout(profiles_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.setPlaceholderText("— выберите профиль —")
        profiles_layout.addWidget(self.profile_combo)
        
        btn_layout = QHBoxLayout()
        self.btn_load_profile = QPushButton("📂 Загрузить")
        self.btn_edit_profile = QPushButton("✏️ Редакт.")
        self.btn_delete_profile = QPushButton("🗑️ Удалить")
        self.chk_confirm_delete = QCheckBox("Подтвердить удаление")
        
        btn_layout.addWidget(self.btn_load_profile)
        btn_layout.addWidget(self.btn_edit_profile)
        btn_layout.addWidget(self.chk_confirm_delete)
        btn_layout.addWidget(self.btn_delete_profile)
        profiles_layout.addLayout(btn_layout)
        
        layout.addWidget(profiles_group)
        
        # --- Birth Data Group ---
        birth_group = QGroupBox("📅 Данные рождения")
        birth_layout = QFormLayout(birth_group)
        
        self.edit_name = QLineEdit("Иван")
        birth_layout.addRow("Имя:", self.edit_name)
        
        date_layout = QHBoxLayout()
        self.edit_birth_date = QDateEdit()
        self.edit_birth_date.setDate(QDate(1990, 5, 15))
        self.edit_birth_date.setCalendarPopup(True)
        self.edit_birth_date.setMinimumDate(QDate(1900, 1, 1))
        self.edit_birth_date.setMaximumDate(QDate(2100, 12, 31))
        date_layout.addWidget(self.edit_birth_date)
        
        self.edit_birth_time = QTimeEdit()
        self.edit_birth_time.setTime(QTime(14, 30))
        date_layout.addWidget(self.edit_birth_time)
        birth_layout.addRow("Дата / Время:", date_layout)
        
        layout.addWidget(birth_group)
        
        # --- City Selection Group ---
        city_group = QGroupBox("🏙️ Город рождения")
        city_layout = QVBoxLayout(city_group)
        city_layout.setSpacing(6)
        
        # Source radio buttons
        self.radio_city = QRadioButton("Из города")
        self.radio_manual = QRadioButton("Вручную")
        self.radio_city.setChecked(True)
        source_group = QButtonGroup(self)
        source_group.addButton(self.radio_city)
        source_group.addButton(self.radio_manual)
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.radio_city)
        source_layout.addWidget(self.radio_manual)
        city_layout.addLayout(source_layout)
        
        # City search
        self.edit_city_query = QLineEdit()
        self.edit_city_query.setPlaceholderText("Поиск города...")
        self.city_completer = CityCompleter(self._city_controller, self)
        self.edit_city_query.setCompleter(self.city_completer)
        city_layout.addWidget(self.edit_city_query)
        
        self.combo_city = QComboBox()
        self.combo_city.setEditable(False)
        self.combo_city.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_city.setMinimumContentsLength(20)
        city_layout.addWidget(self.combo_city)
        
        self.lbl_city_info = QLabel("")
        city_layout.addWidget(self.lbl_city_info)
        
        # Manual coordinates (collapsible)
        self.manual_coords_header = QToolButton()
        self.manual_coords_header.setText("▶ Ручные координаты")
        self.manual_coords_header.setCheckable(True)
        self.manual_coords_header.setChecked(False)
        self.manual_coords_header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.manual_coords_header.setStyleSheet("QToolButton { text-align: left; font-weight: bold; }")
        city_layout.addWidget(self.manual_coords_header)
        
        manual_widget = QWidget()
        manual_layout = QFormLayout(manual_widget)
        manual_layout.setContentsMargins(10, 5, 0, 0)
        
        # Latitude and Longitude in one row
        coords_widget = QWidget()
        coords_layout = QHBoxLayout(coords_widget)
        coords_layout.setContentsMargins(0, 0, 0, 0)
        
        self.spin_latitude = QDoubleSpinBox()
        self.spin_latitude.setRange(-90, 90)
        self.spin_latitude.setDecimals(4)
        self.spin_latitude.setValue(55.7558)
        self.spin_latitude.setFixedWidth(100)
        coords_layout.addWidget(QLabel("Широта:"))
        coords_layout.addWidget(self.spin_latitude)
        
        coords_layout.addSpacing(20)
        
        self.spin_longitude = QDoubleSpinBox()
        self.spin_longitude.setRange(-180, 180)
        self.spin_longitude.setDecimals(4)
        self.spin_longitude.setValue(37.6173)
        self.spin_longitude.setFixedWidth(100)
        coords_layout.addWidget(QLabel("Долгота:"))
        coords_layout.addWidget(self.spin_longitude)
        
        coords_layout.addStretch()
        manual_layout.addRow("Координаты:", coords_widget)
        
        self.spin_utc_offset = QDoubleSpinBox()
        self.spin_utc_offset.setRange(-12, 14)
        self.spin_utc_offset.setDecimals(1)
        self.spin_utc_offset.setValue(3.0)
        manual_layout.addRow("UTC (ч):", self.spin_utc_offset)
        self.spin_utc_offset.setValue(3.0)
        manual_layout.addRow("UTC (ч):", self.spin_utc_offset)
        
        manual_widget.setVisible(False)
        city_layout.addWidget(manual_widget)
        self.manual_widget = manual_widget
        
        # Connect toggle
        self.manual_coords_header.toggled.connect(self._on_manual_coords_toggled)
        
        layout.addWidget(city_group)
        
        # Connect signals for city/manual toggle
        self.radio_city.toggled.connect(self._on_coord_source_changed)
        self.combo_city.currentIndexChanged.connect(self._on_city_selected)
        self.edit_city_query.textChanged.connect(self._on_city_query_changed)
        # Connect completer activated signal to update combo box
        self.city_completer.activated.connect(self._on_completer_activated)
        
        # Initial population of city combo
        self._populate_initial_cities()
        
        # --- Save Profile Buttons ---
        self.btn_save_profile = QPushButton("💾 Сохранить как профиль")
        self.btn_save_changes = QPushButton("💾 Сохранить изменения")
        self.btn_cancel_edit = QPushButton("Отмена")
        
        save_layout = QHBoxLayout()
        save_layout.addWidget(self.btn_save_profile)
        save_layout.addWidget(self.btn_save_changes)
        save_layout.addWidget(self.btn_cancel_edit)
        layout.addLayout(save_layout)
        
        self.btn_save_changes.setVisible(False)
        self.btn_cancel_edit.setVisible(False)
        
        # --- Display Profile Group ---
        display_group = QGroupBox("🎨 Профиль отображения")
        display_layout = QVBoxLayout(display_group)
        
        self.combo_display_profile = QComboBox()
        display_layout.addWidget(self.combo_display_profile)
        
        self.edit_display_profile_name = QLineEdit()
        self.edit_display_profile_name.setPlaceholderText("Имя для сохранения")
        display_layout.addWidget(self.edit_display_profile_name)
        
        # Label visibility options
        label_group = QGroupBox("Подписи на карте")
        label_layout = QGridLayout(label_group)
        
        self.chk_show_planet_labels = QCheckBox("Планеты")
        self.chk_show_planet_labels.setChecked(True)
        label_layout.addWidget(self.chk_show_planet_labels, 0, 0)
        self.chk_show_asteroid_labels = QCheckBox("Астеройды (Хирон)")
        self.chk_show_asteroid_labels.setChecked(True)
        label_layout.addWidget(self.chk_show_asteroid_labels, 0, 1)
        self.chk_show_node_labels = QCheckBox("Узлы (Раху / Кету)")
        self.chk_show_node_labels.setChecked(True)
        label_layout.addWidget(self.chk_show_node_labels, 1, 0)
        self.chk_show_angle_labels = QCheckBox("ASC / MC")
        self.chk_show_angle_labels.setChecked(True)
        label_layout.addWidget(self.chk_show_angle_labels, 1, 1)
        
        display_layout.addWidget(label_group)
        
        dp_btn_layout = QHBoxLayout()
        self.btn_apply_display_profile = QPushButton("📥 Применить")
        self.btn_save_display_profile = QPushButton("💾 Сохранить")
        dp_btn_layout.addWidget(self.btn_apply_display_profile)
        dp_btn_layout.addWidget(self.btn_save_display_profile)
        display_layout.addLayout(dp_btn_layout)
        
        layout.addWidget(display_group)
        
        # --- Additional Settings Group ---
        settings_group = QGroupBox("⚙️ Дополнительные настройки")
        settings_layout = QFormLayout(settings_group)
        
        self.combo_house_system = QComboBox()
        self.combo_house_system.addItems(["placidus", "koch", "equal", "whole_sign", "porphyry"])
        settings_layout.addRow("Дома:", self.combo_house_system)
        
        self.radio_tropical = QRadioButton("Тропический")
        self.radio_sidereal = QRadioButton("Сидерический")
        self.radio_tropical.setChecked(True)
        zodiac_group = QButtonGroup(self)
        zodiac_group.addButton(self.radio_tropical)
        zodiac_group.addButton(self.radio_sidereal)
        zodiac_layout = QHBoxLayout()
        zodiac_layout.addWidget(self.radio_tropical)
        zodiac_layout.addWidget(self.radio_sidereal)
        settings_layout.addRow("Зодиак:", zodiac_layout)
        
        self.combo_ayanamsha = QComboBox()
        self.combo_ayanamsha.addItems(["Лахири", "Раман", "Кришнамурти", "Фаган-Брэдли"])
        self.combo_ayanamsha.setEnabled(False)
        settings_layout.addRow("Аянамша:", self.combo_ayanamsha)
        
        self.chk_chiron = QCheckBox("Хирон")
        self.chk_chiron.setChecked(True)
        self.chk_nodes = QCheckBox("Лунные узлы")
        self.chk_nodes.setChecked(True)
        self.chk_fortune = QCheckBox("Колесо Фортуны")
        self.chk_fortune.setChecked(True)
        self.chk_angles = QCheckBox("ASC/MC")
        self.chk_angles.setChecked(True)
        self.chk_dsc = QCheckBox("DSC")
        self.chk_dsc.setChecked(True)
        obj_layout = QGridLayout()
        obj_layout.addWidget(self.chk_chiron, 0, 0)
        obj_layout.addWidget(self.chk_nodes, 0, 1)
        obj_layout.addWidget(self.chk_fortune, 0, 2)
        obj_layout.addWidget(self.chk_angles, 1, 0)
        obj_layout.addWidget(self.chk_dsc, 1, 1)
        settings_layout.addRow("Объекты:", obj_layout)
        
        self.edit_ephe_path = QLineEdit("ephe")
        settings_layout.addRow("Путь к эфемеридам:", self.edit_ephe_path)
        
        layout.addWidget(settings_group)
        
        # --- Calculate Button ---
        self.btn_calculate = QPushButton("🔮 Рассчитать карту")
        self.btn_calculate.setDefault(True)
        self.btn_calculate.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(self.btn_calculate)
        
        # Connect signals
        self._connect_signals()
        
        # Initial state
        self._on_coord_source_changed()
        self.radio_sidereal.toggled.connect(self._on_zodiac_changed)
        
    def _connect_signals(self):
        self.btn_load_profile.clicked.connect(
            lambda: self.profile_load_requested.emit(self.profile_combo.currentText())
        )
        self.btn_edit_profile.clicked.connect(
            lambda: self.profile_edit_requested.emit(self.profile_combo.currentText())
        )
        self.btn_delete_profile.clicked.connect(self._on_delete_profile)
        self.btn_save_profile.clicked.connect(lambda: self.profile_save_requested.emit(None))
        self.btn_save_changes.clicked.connect(
            lambda: self.profile_save_requested.emit(self._editing_profile_name)
        )
        self.btn_cancel_edit.clicked.connect(self._on_cancel_edit)
        self.btn_apply_display_profile.clicked.connect(
            lambda: self.display_profile_apply_requested.emit(self.combo_display_profile.currentText())
        )
        self.btn_save_display_profile.clicked.connect(self._on_save_display_profile)
        self.btn_calculate.clicked.connect(self._on_calculate)
        
        # Auto-recalc on settings change
        for widget in [
            self.combo_house_system, self.radio_tropical, self.radio_sidereal,
            self.combo_ayanamsha, self.chk_chiron, self.chk_nodes,
            self.chk_fortune, self.chk_angles, self.chk_dsc,
            self.chk_show_planet_labels, self.chk_show_asteroid_labels,
            self.chk_show_node_labels, self.chk_show_angle_labels
        ]:
            if hasattr(widget, 'currentIndexChanged'):
                widget.currentIndexChanged.connect(self.recalc_triggered.emit)
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(self.recalc_triggered.emit)
            elif hasattr(widget, 'stateChanged'):
                widget.stateChanged.connect(self.recalc_triggered.emit)
                
    def _on_city_query_changed(self, text: str):
        """Update city completer and combo when query changes."""
        if text.strip():
            cities = self._city_controller.search_cities(text, limit=20)
        else:
            cities = self._city_controller.get_all_cities()[:20]
            
        # Update completer
        display_names = [self._city_controller.get_city_display_name(c) for c in cities]
        model = QStringListModel(display_names, self)
        self.city_completer.setModel(model)
        
        # Update combo box
        self.combo_city.blockSignals(True)
        self.combo_city.clear()
        for name in display_names:
            self.combo_city.addItem(name)
        self.combo_city.blockSignals(False)
        
    def _populate_initial_cities(self):
        """Populate city combo with initial cities on startup."""
        cities = self._city_controller.get_all_cities()[:20]
        display_names = [self._city_controller.get_city_display_name(c) for c in cities]
        self.combo_city.blockSignals(True)
        self.combo_city.clear()
        for name in display_names:
            self.combo_city.addItem(name)
        self.combo_city.blockSignals(False)
        
    def _on_completer_activated(self, text: str):
        """Handle completer selection - update combo box."""
        self.combo_city.blockSignals(True)
        self.combo_city.setCurrentText(text)
        self.combo_city.blockSignals(False)
        # Also trigger city selection logic
        self._on_city_selected(self.combo_city.currentIndex())
        
    def _load_profiles(self):
        """Load birth profiles into combo."""
        self.profile_combo.clear()
        profiles = self._profile_controller.list_profiles()
        for p in profiles:
            self.profile_combo.addItem(p.name)
            
    def _load_display_profiles(self):
        """Load display profiles into combo."""
        self.combo_display_profile.clear()
        profiles = self._profile_controller.list_profiles()
        # Actually we need display profiles from display profile controller
        # For now, add built-in ones
        self.combo_display_profile.addItems(["classic", "vedic", "minimal", "full"])
        # Профиль по умолчанию — "full" (все объекты),
        # чтобы на карте отображались все планеты, Хирон и узлы.
        self.combo_display_profile.setCurrentText("full")
            
    def _on_coord_source_changed(self):
        use_city = self.radio_city.isChecked()
        self.edit_city_query.setEnabled(use_city)
        self.combo_city.setEnabled(use_city)
        self.manual_widget.setEnabled(not use_city)
        if use_city:
            self._sync_city_info()
        else:
            self.lbl_city_info.setVisible(False)
        
    def set_object_flags(self, objects: dict, appearance: dict = None):
        """Выставляет галочки объектов и подписей из профиля отображения (итерация 20)."""
        if "Chiron" in objects:
            self.chk_chiron.setChecked(bool(objects["Chiron"]))
        if "LunarNodes" in objects:
            self.chk_nodes.setChecked(bool(objects["LunarNodes"]))
        if "PartOfFortune" in objects:
            self.chk_fortune.setChecked(bool(objects["PartOfFortune"]))
        if "Angles" in objects:
            self.chk_angles.setChecked(bool(objects["Angles"]))
            self.chk_dsc.setChecked(bool(objects["Angles"]))
        if appearance:
            pairs = (
                ("show_planet_labels", self.chk_show_planet_labels),
                ("show_asteroid_labels", self.chk_show_asteroid_labels),
                ("show_node_labels", self.chk_show_node_labels),
                ("show_angle_labels", self.chk_show_angle_labels),
            )
            for key, box in pairs:
                if key in appearance:
                    box.setChecked(bool(appearance[key]))

    def _find_city_by_coords(self, lat, lon):
        """Ищет город по координатам (для старых профилей без города)."""
        try:
            for city in self._city_controller.get_all_cities():
                if abs(city.latitude - lat) < 0.01 and abs(city.longitude - lon) < 0.01:
                    return city
        except Exception:
            pass
        return None

    def _sync_city_info(self):
        """Скрывает пустую строку информации о городе (убирает пустой зазор)."""
        self.lbl_city_info.setVisible(bool(self.lbl_city_info.text().strip()))

    def _on_manual_coords_toggled(self, checked: bool):
        """Toggle manual coordinates visibility."""
        self.manual_widget.setVisible(checked)
        self.manual_coords_header.setText(("▼ " if checked else "▶ ") + "Ручные координаты")
        
    def _on_zodiac_changed(self):
        self.combo_ayanamsha.setEnabled(self.radio_sidereal.isChecked())
        
    def _on_city_selected(self, index: int):
        if index < 0:
            return
            
        city_name = self.combo_city.currentText()
        city = self._city_controller.get_city_by_name(city_name)
        if city:
            self.spin_latitude.setValue(city.latitude)
            self.spin_longitude.setValue(city.longitude)
            
            # Update UTC offset from timezone
            from datetime import datetime
            birth_date = self.edit_birth_date.date().toPyDate()
            birth_time = self.edit_birth_time.time().toPyTime()
            dt = datetime.combine(birth_date, birth_time)
            tz_info = self._city_controller.get_timezone_info(city, dt)
            self.spin_utc_offset.setValue(tz_info["utc_offset"])
            
            self.lbl_city_info.setText(
            f"🏙️ {city.name}, {city.country} · "
            f"{city.latitude:.2f}, {city.longitude:.2f} · "
            f"UTC{tz_info['utc_offset']:+.1f}"
        )
        self._sync_city_info()
            
    def _on_delete_profile(self):
        name = self.profile_combo.currentText()
        if not name:
            return
        if not self.chk_confirm_delete.isChecked():
            QMessageBox.warning(self, "Подтверждение", "Поставьте галочку 'Подтвердить удаление'")
            return
            
        reply = QMessageBox.question(
            self, "Удалить профиль",
            f"Удалить профиль '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_delete_requested.emit(name)
            self.chk_confirm_delete.setChecked(False)
            
    def _on_cancel_edit(self):
        self._editing_profile_name = None
        self.btn_save_profile.setVisible(True)
        self.btn_save_changes.setVisible(False)
        self.btn_cancel_edit.setVisible(False)
        
    def _on_save_display_profile(self):
        name = self.edit_display_profile_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя профиля отображения")
            return
        self.display_profile_save_requested.emit(name)
        
    def _on_calculate(self):
        """Emit calculate signal with current form data."""
        birth_data = self.get_birth_data()
        settings = self.get_settings()
        display_profile = self.combo_display_profile.currentText()
        self.calculate_requested.emit(birth_data, settings, display_profile)
        
    def get_birth_data(self) -> dict:
        """Get birth data from form."""
        # Get city info from combo box
        city_text = self.combo_city.currentText().strip()
        city_parts = city_text.split(", ")
        city_name = city_parts[0] if city_parts else ""
        city_country = city_parts[1] if len(city_parts) > 1 else ""
        
        return {
            "name": self.edit_name.text().strip() or "Chart",
            "date": self.edit_birth_date.date().toPyDate().strftime("%Y-%m-%d"),
            "time": self.edit_birth_time.time().toPyTime().strftime("%H:%M"),
            "latitude": self.spin_latitude.value(),
            "longitude": self.spin_longitude.value(),
            "utc_offset_hours": self.spin_utc_offset.value(),
            "city_name": city_name,
            "city_country": city_country,
            "city_timezone": self.lbl_city_info.text().replace("Часовой пояс: ", "") if "Часовой пояс:" in self.lbl_city_info.text() else "",
        }
        
    def get_settings(self) -> dict:
        """Get calculation settings from form."""
        zodiac = "sidereal" if self.radio_sidereal.isChecked() else "tropical"
        ayanamsha_map = {
            "Лахири": "lahiri", "Раман": "raman",
            "Кришнамурти": "krishnamurti", "Фаган-Брэдли": "fagan_brady"
        }
        return {
            "house_system": self.combo_house_system.currentText(),
            "zodiac": zodiac,
            "ayanamsha": ayanamsha_map.get(self.combo_ayanamsha.currentText(), "lahiri"),
            "include_chiron": self.chk_chiron.isChecked(),
            "include_nodes": self.chk_nodes.isChecked(),
            "include_part_of_fortune": self.chk_fortune.isChecked(),
            "include_angles": self.chk_angles.isChecked(),
            "include_dsc": self.chk_dsc.isChecked(),
            "show_planet_labels": self.chk_show_planet_labels.isChecked(),
            "show_asteroid_labels": self.chk_show_asteroid_labels.isChecked(),
            "show_node_labels": self.chk_show_node_labels.isChecked(),
            "show_angle_labels": self.chk_show_angle_labels.isChecked(),
            "ephe_path": self.edit_ephe_path.text() or None,
        }
        
    def set_birth_data(self, birth_data: dict):
        """Set form fields from birth data."""
        self.edit_name.setText(birth_data.get("name", ""))
        
        if "date" in birth_data:
            self.edit_birth_date.setDate(QDate.fromString(birth_data["date"], "yyyy-MM-dd"))
        if "time" in birth_data:
            self.edit_birth_time.setTime(QTime.fromString(birth_data["time"], "HH:mm"))
            
        self.spin_latitude.setValue(birth_data.get("latitude", 0))
        self.spin_longitude.setValue(birth_data.get("longitude", 0))
        self.spin_utc_offset.setValue(birth_data.get("utc_offset_hours", 0))
        
        # Set city if available (итерация 19: город восстанавливается в список)
        city_name = birth_data.get("city_name", "")
        city_country = birth_data.get("city_country", "")
        if not city_name:
            found = self._find_city_by_coords(
                birth_data.get("latitude", 0), birth_data.get("longitude", 0))
            if found is not None:
                city_name = found.name
                city_country = found.country
        if city_name:
            display_name = f"{city_name}, {city_country}" if city_country else city_name
            self.edit_city_query.setText(display_name)
            self._on_city_query_changed(city_name)
            idx = self.combo_city.findText(display_name)
            if idx < 0:
                self.combo_city.insertItem(0, display_name)
                idx = 0
            self.combo_city.setCurrentIndex(idx)
            self._on_city_selected(idx)
        else:
            self.lbl_city_info.setText("")
        self._sync_city_info()
        
    def set_editing_profile(self, name: str):
        """Set editing mode for a profile."""
        self._editing_profile_name = name
        self.btn_save_profile.setVisible(False)
        self.btn_save_changes.setVisible(True)
        self.btn_cancel_edit.setVisible(True)
        
    def clear_editing_profile(self):
        self._editing_profile_name = None
        self.btn_save_profile.setVisible(True)
        self.btn_save_changes.setVisible(False)
        self.btn_cancel_edit.setVisible(False)
        
    def get_coord_source(self) -> str:
        return "city" if self.radio_city.isChecked() else "manual"