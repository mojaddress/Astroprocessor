"""
Transit Panel - Widget for transit calculations and results.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QRadioButton, QButtonGroup, QDateEdit, QComboBox, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, pyqtSlot
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

from astro_core.controllers import TransitController, CityController
from astro_core.controllers.city_controller import City
from astro_core.constants import DEFAULT_TRANSIT_PLANETS, ASPECT_DEFINITIONS


class TransitPanel(QWidget):
    """Panel for transit calculations."""
    
    # Signals
    calculate_requested = pyqtSignal(str, date, date, List[str], List[str])  # mode, start, end, planets, aspects
    
    def __init__(
        self,
        transit_controller: TransitController,
        city_controller: CityController,
        parent=None
    ):
        super().__init__(parent)
        self._transit_controller = transit_controller
        self._city_controller = city_controller
        self._natal_objects: List[Dict] = []
        self._transit_city: Optional[City] = None
        self._chart_settings: Dict = {}
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # --- Mode Selection ---
        mode_group = QGroupBox("Режим расчёта")
        mode_layout = QVBoxLayout(mode_group)
        
        self.radio_calendar = QRadioButton("Быстрый (по дням)")
        self.radio_precise = QRadioButton("Точный (с временем аспектов)")
        self.radio_periods = QRadioButton("Периоды активности")
        self.radio_calendar.setChecked(True)
        
        mode_btn_group = QButtonGroup(self)
        mode_btn_group.addButton(self.radio_calendar)
        mode_btn_group.addButton(self.radio_precise)
        mode_btn_group.addButton(self.radio_periods)
        
        mode_layout.addWidget(self.radio_calendar)
        mode_layout.addWidget(self.radio_precise)
        mode_layout.addWidget(self.radio_periods)
        layout.addWidget(mode_group)
        
        # --- Filters ---
        filter_group = QGroupBox("Фильтры")
        filter_layout = QFormLayout(filter_group)
        
        self.combo_planets = QComboBox()
        self.combo_planets.setPlaceholderText("Все планеты")
        # Will be populated when chart is calculated
        filter_layout.addRow("Транзитные планеты:", self.combo_planets)
        
        self.combo_aspects = QComboBox()
        self.combo_aspects.setPlaceholderText("Все аспекты")
        aspect_names = [a["name"] for a in ASPECT_DEFINITIONS]
        self.combo_aspects.addItems(aspect_names)
        filter_layout.addRow("Аспекты:", self.combo_aspects)
        
        layout.addWidget(filter_group)
        
        # --- Date Selection ---
        date_group = QGroupBox("📅 Дата транзита")
        date_layout = QVBoxLayout(date_group)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.btn_minus_month = QPushButton("⏪ -1 мес")
        self.btn_minus_day = QPushButton("◀️ -1 день")
        self.btn_plus_day = QPushButton("+1 день ▶️")
        self.btn_plus_month = QPushButton("+1 мес ⏩")
        nav_layout.addWidget(self.btn_minus_month)
        nav_layout.addWidget(self.btn_minus_day)
        nav_layout.addWidget(self.btn_plus_day)
        nav_layout.addWidget(self.btn_plus_month)
        date_layout.addLayout(nav_layout)
        
        self.edit_transit_date = QDateEdit()
        self.edit_transit_date.setDate(QDate.currentDate())
        self.edit_transit_date.setCalendarPopup(True)
        date_layout.addWidget(self.edit_transit_date)
        
        layout.addWidget(date_group)
        
        # --- Transit City ---
        city_group = QGroupBox("🏙️ Город транзита")
        city_layout = QVBoxLayout(city_group)
        
        self.radio_no_city = QRadioButton("Без города")
        self.radio_with_city = QRadioButton("Выбрать город")
        self.radio_no_city.setChecked(True)
        city_source_group = QButtonGroup(self)
        city_source_group.addButton(self.radio_no_city)
        city_source_group.addButton(self.radio_with_city)
        
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.radio_no_city)
        source_layout.addWidget(self.radio_with_city)
        city_layout.addLayout(source_layout)
        
        self.edit_transit_city_query = QLineEdit()
        self.edit_transit_city_query.setPlaceholderText("Поиск города транзита...")
        city_layout.addWidget(self.edit_transit_city_query)
        
        self.combo_transit_city = QComboBox()
        city_layout.addWidget(self.combo_transit_city)
        
        self.lbl_transit_city_info = QLabel("")
        city_layout.addWidget(self.lbl_transit_city_info)
        
        layout.addWidget(city_group)
        
        # --- Period Type ---
        period_group = QGroupBox("Тип периода")
        period_layout = QVBoxLayout(period_group)
        
        self.radio_single_date = QRadioButton("Одна дата")
        self.radio_date_range = QRadioButton("Диапазон дат")
        self.radio_date_range.setChecked(True)
        period_btn_group = QButtonGroup(self)
        period_btn_group.addButton(self.radio_single_date)
        period_btn_group.addButton(self.radio_date_range)
        
        period_layout.addWidget(self.radio_single_date)
        period_layout.addWidget(self.radio_date_range)
        
        self.edit_start_date = QDateEdit()
        self.edit_start_date.setDate(QDate.currentDate())
        self.edit_start_date.setCalendarPopup(True)
        self.edit_end_date = QDateEdit()
        self.edit_end_date.setDate(QDate.currentDate().addDays(7))
        self.edit_end_date.setCalendarPopup(True)
        
        period_form = QFormLayout()
        period_form.addRow("Начало:", self.edit_start_date)
        period_form.addRow("Конец:", self.edit_end_date)
        period_layout.addLayout(period_form)
        
        layout.addWidget(period_group)
        
        # --- Calculate Button ---
        self.btn_calculate = QPushButton("🔮 Рассчитать транзиты")
        self.btn_calculate.setDefault(True)
        self.btn_calculate.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(self.btn_calculate)
        
        # --- Results Table ---
        results_group = QGroupBox("Результаты")
        results_layout = QVBoxLayout(results_group)
        
        self.table_results = QTableWidget()
        self.table_results.setAlternatingRowColors(True)
        self.table_results.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_results.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.table_results)
        
        self.btn_export_json = QPushButton("📥 Экспорт JSON")
        results_layout.addWidget(self.btn_export_json)
        
        layout.addWidget(results_group)
        
        # Connect signals
        self._connect_signals()
        
        # Initial state
        self._on_period_type_changed()
        self._on_transit_city_mode_changed()
        
    def _connect_signals(self):
        self.btn_minus_month.clicked.connect(lambda: self._shift_date(-30))
        self.btn_minus_day.clicked.connect(lambda: self._shift_date(-1))
        self.btn_plus_day.clicked.connect(lambda: self._shift_date(1))
        self.btn_plus_month.clicked.connect(lambda: self._shift_date(30))
        
        self.radio_single_date.toggled.connect(self._on_period_type_changed)
        self.radio_date_range.toggled.connect(self._on_period_type_changed)
        
        self.radio_no_city.toggled.connect(self._on_transit_city_mode_changed)
        self.radio_with_city.toggled.connect(self._on_transit_city_mode_changed)
        self.edit_transit_city_query.textChanged.connect(self._on_transit_city_query_changed)
        self.combo_transit_city.currentIndexChanged.connect(self._on_transit_city_selected)
        
        self.btn_calculate.clicked.connect(self._on_calculate)
        self.btn_export_json.clicked.connect(self._on_export_json)
        
    def _on_period_type_changed(self):
        single = self.radio_single_date.isChecked()
        self.edit_start_date.setEnabled(not single)
        self.edit_end_date.setEnabled(not single)
        if single:
            self.edit_start_date.setDate(self.edit_transit_date.date())
            self.edit_end_date.setDate(self.edit_transit_date.date())
            
    def _on_transit_city_mode_changed(self):
        use_city = self.radio_with_city.isChecked()
        self.edit_transit_city_query.setEnabled(use_city)
        self.combo_transit_city.setEnabled(use_city)
        self.lbl_transit_city_info.setVisible(use_city)
        
    def _shift_date(self, days: int):
        current = self.edit_transit_date.date()
        new_date = current.addDays(days)
        self.edit_transit_date.setDate(new_date)
        
    def _on_transit_city_query_changed(self, text: str):
        if text.strip():
            cities = self._city_controller.search_cities(text, limit=20)
        else:
            cities = self._city_controller.get_all_cities()[:20]
            
        self.combo_transit_city.clear()
        for c in cities:
            self.combo_transit_city.addItem(
                self._city_controller.get_city_display_name(c)
            )
            
    def _on_transit_city_selected(self, index: int):
        if index < 0:
            self._transit_city = None
            return
            
        city_name = self.combo_transit_city.currentText()
        city = self._city_controller.get_city_by_name(city_name)
        if city:
            self._transit_city = city
            self.lbl_transit_city_info.setText(
                f"📍 {city.name}, {city.country}"
            )
            
    def set_natal_data(self, natal_objects: List[Dict], chart_settings: Dict):
        """Set natal chart data for transit calculations."""
        self._natal_objects = natal_objects
        self._chart_settings = chart_settings
        
        # Update planet filter combo with enabled planets from chart
        enabled_planets = chart_settings.get("enabled_planets", DEFAULT_TRANSIT_PLANETS)
        self.combo_planets.clear()
        for p in enabled_planets:
            self.combo_planets.addItem(p)
            
    def _on_calculate(self):
        """Emit calculate signal with current settings."""
        if not self._natal_objects:
            QMessageBox.warning(self, "Ошибка", "Сначала рассчитайте натальную карту")
            return
            
        # Get mode
        if self.radio_calendar.isChecked():
            mode = "calendar"
        elif self.radio_precise.isChecked():
            mode = "precise"
        else:
            mode = "periods"
            
        # Get dates
        if self.radio_single_date.isChecked():
            start_date = self.edit_transit_date.date().toPyDate()
            end_date = start_date
        else:
            start_date = self.edit_start_date.date().toPyDate()
            end_date = self.edit_end_date.date().toPyDate()
            
        # Get filters
        planets = [self.combo_planets.currentText()] if self.combo_planets.currentText() else []
        aspects = [self.combo_aspects.currentText()] if self.combo_aspects.currentText() else []
        
        self.calculate_requested.emit(mode, start_date, end_date, planets, aspects)
        
    def _on_export_json(self):
        """Export results to JSON."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        if self.table_results.rowCount() == 0:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить транзиты", "transits.json", "JSON Files (*.json)"
        )
        if file_path:
            # Collect data from table
            data = []
            for row in range(self.table_results.rowCount()):
                row_data = {}
                for col in range(self.table_results.columnCount()):
                    header = self.table_results.horizontalHeaderItem(col)
                    item = self.table_results.item(row, col)
                    if header and item:
                        row_data[header.text()] = item.text()
                data.append(row_data)
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
    @pyqtSlot(list)
    def set_results(self, results: List[Dict]):
        """Display transit results in table."""
        self.table_results.setRowCount(0)
        
        if not results:
            return
            
        # Determine columns from first result
        columns = list(results[0].keys())
        self.table_results.setColumnCount(len(columns))
        self.table_results.setHorizontalHeaderLabels(columns)
        
        # Translate column headers to Russian
        header_map = {
            "date": "Дата",
            "transit_planet": "Транзитная планета",
            "aspect": "Аспект",
            "natal_point": "Натальная точка",
            "orb": "Орб",
            "strength": "Сила",
            "exact_datetime": "Точное время",
            "direction": "Направление",
            "start_date": "Вход в орб",
            "exact_date": "Пик",
            "end_date": "Выход из орба",
        }
        
        for i, col in enumerate(columns):
            if col in header_map:
                self.table_results.setHorizontalHeaderItem(i, QTableWidgetItem(header_map[col]))
                
        self.table_results.setRowCount(len(results))
        
        for row, result in enumerate(results):
            for col, key in enumerate(columns):
                value = result.get(key, "")
                if isinstance(value, float):
                    item = QTableWidgetItem(f"{value:.2f}")
                else:
                    item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_results.setItem(row, col, item)
                
        self.table_results.resizeColumnsToContents()