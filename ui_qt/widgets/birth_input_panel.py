"""
Birth Input Panel - Widget for entering birth data.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QDateEdit, QTimeEdit, QDoubleSpinBox, QComboBox,
    QRadioButton, QButtonGroup, QPushButton, QLabel, QCheckBox,
    QCompleter, QStringListModel, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QStringListModel
from datetime import date, time
from typing import Optional, List, Callable

from astro_core.controllers import CityController, ProfileController
from astro_core.controllers.city_controller import City


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
        city_layout.addWidget(self.combo_city)
        
        self.lbl_city_info = QLabel("")
        city_layout.addWidget(self.lbl_city_info)
        
        # Manual coordinates
        manual_widget = QWidget()
        manual_layout = QFormLayout(manual_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        
        self.spin_latitude = QDoubleSpinBox()
        self.spin_latitude.setRange(-90, 90)
        self.spin_latitude.setDecimals(4)
        self.spin_latitude.setValue(55.7558)
        manual_layout.addRow("Широта:", self.spin_latitude)
        
        self.spin_longitude = QDoubleSpinBox()
        self.spin_longitude.setRange(-180, 180)
        self.spin_longitude.setDecimals(4)
        self.spin_longitude.setValue(37.6173)
        manual_layout.addRow("Долгота:", self.spin_longitude)
        
        self.spin_utc_offset = QDoubleSpinBox()
        self.spin_utc_offset.setRange(-12, 14)
        self.spin_utc_offset.setDecimals(1)
        self.spin_utc_offset.setValue(3.0)
        manual_layout.addRow("UTC (ч):", self.spin_utc_offset)
        
        city_layout.addWidget(manual_widget)
        self.manual_widget = manual_widget
        
        layout.addWidget(city_group)
        
        # Connect signals for city/manual toggle
        self.radio_city.toggled.connect(self._on_coord_source_changed)
        self.combo_city.currentIndexChanged.connect(self._on_city_selected)
        self.edit_city_query.textChanged.connect(self._on_city_query_changed)
        
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
        self.chk_fortune = QCheckBox("Part of Fortune")
        self.chk_fortune.setChecked(True)
        self.chk_angles = QCheckBox("ASC/MC")
        self.chk_angles.setChecked(True)
        
        obj_layout = QHBoxLayout()
        obj_layout.addWidget(self.chk_chiron)
        obj_layout.addWidget(self.chk_nodes)
        obj_layout.addWidget(self.chk_fortune)
        obj_layout.addWidget(self.chk_angles)
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
            self.chk_fortune, self.chk_angles
        ]:
            if hasattr(widget, 'currentIndexChanged'):
                widget.currentIndexChanged.connect(self.recalc_triggered.emit)
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(self.recalc_triggered.emit)
            elif hasattr(widget, 'stateChanged'):
                widget.stateChanged.connect(self.recalc_triggered.emit)
                
    def _load_profiles(self):
        """Load birth profiles into combo."""
        self.profile_combo.clear()
        profiles = self._profile_controller.list_profiles()
        for p in profiles:
            self.profile_combo.addItem(p.name)
            
    def _load_display_profiles(self, profiles: List):
        """Load display profiles into combo."""
        self.combo_display_profile.clear()
        for p in profiles:
            self.combo_display_profile.addItem(p.name)
            
    def _on_coord_source_changed(self):
        use_city = self.radio_city.isChecked()
        self.edit_city_query.setEnabled(use_city)
        self.combo_city.setEnabled(use_city)
        self.manual_widget.setEnabled(not use_city)
        self.lbl_city_info.setVisible(use_city)
        
    def _on_zodiac_changed(self):
        self.combo_ayanamsha.setEnabled(self.radio_sidereal.isChecked())
        
    def _on_city_query_changed(self, text: str):
        """Update city completer when query changes."""
        self.city_completer._update_model(text)
        
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
        return {
            "name": self.edit_name.text().strip() or "Chart",
            "date": self.edit_birth_date.date().toPyDate().strftime("%Y-%m-%d"),
            "time": self.edit_birth_time.time().toPyTime().strftime("%H:%M"),
            "latitude": self.spin_latitude.value(),
            "longitude": self.spin_longitude.value(),
            "utc_offset_hours": self.spin_utc_offset.value(),
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