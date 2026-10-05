"""
Settings Dialog - Application settings.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QLineEdit, QPushButton, QDialogButtonBox, QFileDialog,
    QLabel, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import Optional

from astro_core.state import SettingsManager, AppSettings


class SettingsDialog(QDialog):
    """Application settings dialog."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings_manager = settings_manager
        self._settings = settings_manager.settings
        
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._init_ui()
        self._load_settings()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # General tab
        self.tab_general = self._create_general_tab()
        self.tabs.addTab(self.tab_general, "Общие")
        
        # Calculation tab
        self.tab_calculation = self._create_calculation_tab()
        self.tabs.addTab(self.tab_calculation, "Расчёты")
        
        # Display tab
        self.tab_display = self._create_display_tab()
        self.tabs.addTab(self.tab_display, "Отображение")
        
        # Transit tab
        self.tab_transit = self._create_transit_tab()
        self.tabs.addTab(self.tab_transit, "Транзиты")
        
        # Progression tab
        self.tab_progression = self._create_progression_tab()
        self.tabs.addTab(self.tab_progression, "Прогрессии")
        
        # Paths tab
        self.tab_paths = self._create_paths_tab()
        self.tabs.addTab(self.tab_paths, "Пути")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._on_restore_defaults)
        layout.addWidget(self.button_box)
        
    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.combo_language = QComboBox()
        self.combo_language.addItems(["ru", "en"])
        layout.addRow("Язык:", self.combo_language)
        
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["light", "dark", "auto"])
        layout.addRow("Тема:", self.combo_theme)
        
        self.chk_auto_recalc = QCheckBox("Автоматический пересчёт при изменении настроек")
        layout.addRow(self.chk_auto_recalc)
        
        self.chk_show_warnings = QCheckBox("Показывать предупреждения")
        layout.addRow(self.chk_show_warnings)
        
        self.chk_compact_mode = QCheckBox("Компактный режим")
        layout.addRow(self.chk_compact_mode)
        
        return widget
        
    def _create_calculation_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.combo_house_system = QComboBox()
        self.combo_house_system.addItems(["placidus", "koch", "equal", "whole_sign", "porphyry"])
        layout.addRow("Система домов по умолчанию:", self.combo_house_system)
        
        self.combo_zodiac = QComboBox()
        self.combo_zodiac.addItems(["tropical", "sidereal"])
        layout.addRow("Зодиак по умолчанию:", self.combo_zodiac)
        
        self.combo_ayanamsha = QComboBox()
        self.combo_ayanamsha.addItems(["lahiri", "raman", "krishnamurti", "fagan_brady"])
        layout.addRow("Аянамша по умолчанию:", self.combo_ayanamsha)
        
        self.chk_chiron = QCheckBox("Включать Хирон")
        layout.addRow(self.chk_chiron)
        
        self.chk_nodes = QCheckBox("Включать лунные узлы")
        layout.addRow(self.chk_nodes)
        
        self.chk_fortune = QCheckBox("Включать Part of Fortune")
        layout.addRow(self.chk_fortune)
        
        self.chk_angles = QCheckBox("Включать ASC/MC")
        layout.addRow(self.chk_angles)
        
        return widget
        
    def _create_display_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.combo_display_profile = QComboBox()
        self.combo_display_profile.addItems(["classic", "vedic", "minimal", "full"])
        layout.addRow("Профиль отображения:", self.combo_display_profile)
        
        self.spin_chart_size = QSpinBox()
        self.spin_chart_size.setRange(400, 2000)
        self.spin_chart_size.setSingleStep(100)
        layout.addRow("Размер карты:", self.spin_chart_size)
        
        self.spin_dot_size = QSpinBox()
        self.spin_dot_size.setRange(2, 15)
        layout.addRow("Размер точек:", self.spin_dot_size)
        
        self.combo_label_mode = QComboBox()
        self.combo_label_mode.addItems(["symbols", "words", "both"])
        layout.addRow("Режим подписей:", self.combo_label_mode)
        
        self.chk_show_aspects = QCheckBox("Показывать аспекты")
        layout.addRow(self.chk_show_aspects)
        
        self.chk_show_houses = QCheckBox("Показывать дома")
        layout.addRow(self.chk_show_houses)
        
        return widget
        
    def _create_transit_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.combo_transit_mode = QComboBox()
        self.combo_transit_mode.addItems(["calendar", "precise", "periods"])
        layout.addRow("Режим транзитов:", self.combo_transit_mode)
        
        self.spin_transit_days = QSpinBox()
        self.spin_transit_days.setRange(1, 365)
        layout.addRow("Дней по умолчанию:", self.spin_transit_days)
        
        self.spin_transit_utc = QDoubleSpinBox()
        self.spin_transit_utc.setRange(-12, 14)
        self.spin_transit_utc.setDecimals(1)
        layout.addRow("UTC для транзитов:", self.spin_transit_utc)
        
        return widget
        
    def _create_progression_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.combo_progression_type = QComboBox()
        self.combo_progression_type.addItems(["secondary", "solar_arc"])
        layout.addRow("Тип прогрессий:", self.combo_progression_type)
        
        return widget
        
    def _create_paths_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.edit_profiles_dir = QLineEdit()
        btn_profiles = QPushButton("Обзор...")
        btn_profiles.clicked.connect(lambda: self._browse_dir(self.edit_profiles_dir))
        profiles_layout = QHBoxLayout()
        profiles_layout.addWidget(self.edit_profiles_dir)
        profiles_layout.addWidget(btn_profiles)
        layout.addRow("Папка профилей:", profiles_layout)
        
        self.edit_display_profiles_dir = QLineEdit()
        btn_display_profiles = QPushButton("Обзор...")
        btn_display_profiles.clicked.connect(lambda: self._browse_dir(self.edit_display_profiles_dir))
        display_profiles_layout = QHBoxLayout()
        display_profiles_layout.addWidget(self.edit_display_profiles_dir)
        display_profiles_layout.addWidget(btn_display_profiles)
        layout.addRow("Папка профилей отображения:", display_profiles_layout)
        
        self.edit_cities_file = QLineEdit()
        btn_cities = QPushButton("Обзор...")
        btn_cities.clicked.connect(lambda: self._browse_file(self.edit_cities_file, "JSON Files (*.json)"))
        cities_layout = QHBoxLayout()
        cities_layout.addWidget(self.edit_cities_file)
        cities_layout.addWidget(btn_cities)
        layout.addRow("Файл городов:", cities_layout)
        
        self.edit_ephe_dir = QLineEdit()
        btn_ephe = QPushButton("Обзор...")
        btn_ephe.clicked.connect(lambda: self._browse_dir(self.edit_ephe_dir))
        ephe_layout = QHBoxLayout()
        ephe_layout.addWidget(self.edit_ephe_dir)
        ephe_layout.addWidget(btn_ephe)
        layout.addRow("Папка эфемерид:", ephe_layout)
        
        return widget
        
    def _browse_dir(self, line_edit: QLineEdit):
        dir_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if dir_path:
            line_edit.setText(dir_path)
            
    def _browse_file(self, line_edit: QLineEdit, filter_str: str):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", filter_str)
        if file_path:
            line_edit.setText(file_path)
            
    def _load_settings(self):
        """Load settings into UI."""
        s = self._settings
        
        # General
        self.combo_language.setCurrentText(s.language)
        self.combo_theme.setCurrentText(s.theme)
        self.chk_auto_recalc.setChecked(s.auto_recalculate)
        self.chk_show_warnings.setChecked(s.show_warnings)
        self.chk_compact_mode.setChecked(s.compact_mode)
        
        # Calculation
        self.combo_house_system.setCurrentText(s.default_house_system)
        self.combo_zodiac.setCurrentText(s.default_zodiac)
        self.combo_ayanamsha.setCurrentText(s.default_ayanamsha)
        self.chk_chiron.setChecked(s.default_include_chiron)
        self.chk_nodes.setChecked(s.default_include_nodes)
        self.chk_fortune.setChecked(s.default_include_fortune)
        self.chk_angles.setChecked(s.default_include_angles)
        
        # Display
        self.combo_display_profile.setCurrentText(s.default_display_profile)
        self.spin_chart_size.setValue(s.default_chart_size)
        self.spin_dot_size.setValue(s.default_dot_size)
        self.combo_label_mode.setCurrentText(s.default_label_mode)
        self.chk_show_aspects.setChecked(s.default_show_aspects)
        self.chk_show_houses.setChecked(s.default_show_houses)
        
        # Transit
        self.combo_transit_mode.setCurrentText(s.default_transit_mode)
        self.spin_transit_days.setValue(s.default_transit_days)
        self.spin_transit_utc.setValue(s.default_transit_utc_offset)
        
        # Progression
        self.combo_progression_type.setCurrentText(s.default_progression_type)
        
        # Paths
        self.edit_profiles_dir.setText(s.profiles_dir)
        self.edit_display_profiles_dir.setText(s.display_profiles_dir)
        self.edit_cities_file.setText(s.cities_file)
        self.edit_ephe_dir.setText(s.ephe_dir)
        
    def _collect_settings(self) -> AppSettings:
        """Collect settings from UI."""
        return AppSettings(
            language=self.combo_language.currentText(),
            theme=self.combo_theme.currentText(),
            auto_recalculate=self.chk_auto_recalc.isChecked(),
            show_warnings=self.chk_show_warnings.isChecked(),
            compact_mode=self.chk_compact_mode.isChecked(),
            default_house_system=self.combo_house_system.currentText(),
            default_zodiac=self.combo_zodiac.currentText(),
            default_ayanamsha=self.combo_ayanamsha.currentText(),
            default_include_chiron=self.chk_chiron.isChecked(),
            default_include_nodes=self.chk_nodes.isChecked(),
            default_include_fortune=self.chk_fortune.isChecked(),
            default_include_angles=self.chk_angles.isChecked(),
            default_display_profile=self.combo_display_profile.currentText(),
            default_chart_size=self.spin_chart_size.value(),
            default_dot_size=self.spin_dot_size.value(),
            default_label_mode=self.combo_label_mode.currentText(),
            default_show_aspects=self.chk_show_aspects.isChecked(),
            default_show_houses=self.chk_show_houses.isChecked(),
            default_transit_mode=self.combo_transit_mode.currentText(),
            default_transit_days=self.spin_transit_days.value(),
            default_transit_utc_offset=self.spin_transit_utc.value(),
            default_progression_type=self.combo_progression_type.currentText(),
            profiles_dir=self.edit_profiles_dir.text() or "profiles",
            display_profiles_dir=self.edit_display_profiles_dir.text() or "config/display_profiles",
            cities_file=self.edit_cities_file.text() or "data/cities.json",
            ephe_dir=self.edit_ephe_dir.text() or "ephe",
            log_level=self._settings.log_level,
            max_transit_days_precise=self._settings.max_transit_days_precise,
            max_transit_days_periods=self._settings.max_transit_days_periods,
        )
        
    def _on_accept(self):
        """Save and close."""
        self._on_apply()
        self.accept()
        
    def _on_apply(self):
        """Save settings."""
        settings = self._collect_settings()
        self._settings_manager.settings = settings
        self._settings_manager.save()
        self.settings_changed.emit()
        
    def _on_restore_defaults(self):
        """Restore default settings."""
        self._settings_manager.reset_to_defaults()
        self._load_settings()