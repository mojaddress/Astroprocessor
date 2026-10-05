"""
Progression Panel - Widget for progression calculations.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QRadioButton, QButtonGroup, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QLabel, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, pyqtSlot
from datetime import date
from typing import List, Dict, Any


class ProgressionPanel(QWidget):
    """Panel for progression calculations."""
    
    # Signals
    calculate_requested = pyqtSignal(str, date)  # type, date
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # --- Progression Type ---
        type_group = QGroupBox("Тип прогрессий")
        type_layout = QVBoxLayout(type_group)
        
        self.radio_secondary = QRadioButton("Вторичные (день за год)")
        self.radio_solar_arc = QRadioButton("Солнечная дуга")
        self.radio_secondary.setChecked(True)
        
        type_btn_group = QButtonGroup(self)
        type_btn_group.addButton(self.radio_secondary)
        type_btn_group.addButton(self.radio_solar_arc)
        
        type_layout.addWidget(self.radio_secondary)
        type_layout.addWidget(self.radio_solar_arc)
        layout.addWidget(type_group)
        
        # --- Date ---
        date_group = QGroupBox("Дата прогрессии")
        date_layout = QFormLayout(date_group)
        
        self.edit_progression_date = QDateEdit()
        self.edit_progression_date.setDate(QDate.currentDate())
        self.edit_progression_date.setCalendarPopup(True)
        self.edit_progression_date.setMinimumDate(QDate(1900, 1, 1))
        self.edit_progression_date.setMaximumDate(QDate(2100, 12, 31))
        date_layout.addRow("Дата:", self.edit_progression_date)
        
        layout.addWidget(date_group)
        
        # --- Calculate Button ---
        self.btn_calculate = QPushButton("🔮 Рассчитать прогрессии")
        self.btn_calculate.setDefault(True)
        self.btn_calculate.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(self.btn_calculate)
        
        # --- Results Tabs ---
        self.tab_results = QTabWidget()
        
        # Planets tab
        self.table_planets = QTableWidget()
        self.table_planets.setAlternatingRowColors(True)
        self.table_planets.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_planets.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_planets.horizontalHeader().setStretchLastSection(True)
        self.tab_results.addTab(self.table_planets, "Планеты")
        
        # Points tab
        self.table_points = QTableWidget()
        self.table_points.setAlternatingRowColors(True)
        self.table_points.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_points.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_points.horizontalHeader().setStretchLastSection(True)
        self.tab_results.addTab(self.table_points, "Точки (ASC, MC, PoF)")
        
        # Aspects tab
        self.table_aspects = QTableWidget()
        self.table_aspects.setAlternatingRowColors(True)
        self.table_aspects.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_aspects.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_aspects.horizontalHeader().setStretchLastSection(True)
        self.tab_results.addTab(self.table_aspects, "Аспекты к наталу")
        
        layout.addWidget(self.tab_results)
        
        # --- Export Button ---
        self.btn_export_json = QPushButton("📥 Экспорт JSON")
        layout.addWidget(self.btn_export_json)
        
        # Connect signals
        self.btn_calculate.clicked.connect(self._on_calculate)
        self.btn_export_json.clicked.connect(self._on_export_json)
        
    def _on_calculate(self):
        """Emit calculate signal."""
        progression_type = "secondary" if self.radio_secondary.isChecked() else "solar_arc"
        progression_date = self.edit_progression_date.date().toPyDate()
        self.calculate_requested.emit(progression_type, progression_date)
        
    def _on_export_json(self):
        """Export current tab results to JSON."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        current_widget = self.tab_results.currentWidget()
        if not current_widget or current_widget.rowCount() == 0:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить прогрессии", "progressions.json", "JSON Files (*.json)"
        )
        if file_path:
            data = []
            for row in range(current_widget.rowCount()):
                row_data = {}
                for col in range(current_widget.columnCount()):
                    header = current_widget.horizontalHeaderItem(col)
                    item = current_widget.item(row, col)
                    if header and item:
                        row_data[header.text()] = item.text()
                data.append(row_data)
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
    @pyqtSlot(object)
    def set_results(self, result):
        """Display progression results."""
        # Clear all tables
        self.table_planets.setRowCount(0)
        self.table_points.setRowCount(0)
        self.table_aspects.setRowCount(0)
        
        if not result:
            return
            
        # Planets
        if result.progressed_planets:
            self._populate_table(self.table_planets, result.progressed_planets)
            
        # Points
        if result.progressed_points:
            self._populate_table(self.table_points, result.progressed_points)
            
        # Aspects
        if result.aspects:
            self._populate_table(self.table_aspects, result.aspects)
            
    def _populate_table(self, table: QTableWidget, data: List[Dict]):
        """Populate a table with data."""
        if not data:
            return
            
        columns = list(data[0].keys())
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # Translate headers
        header_map = {
            "name": "Имя",
            "longitude": "Долгота",
            "sign": "Знак",
            "degree": "Градус",
            "house": "Дом",
            "retrograde": "Ретро",
            "speed": "Скорость",
            "progressed_planet": "Прогрессивная планета",
            "aspect": "Аспект",
            "natal_point": "Натальная точка",
            "orb": "Орб",
            "strength": "Сила",
            "applying": "Сходится",
        }
        
        for i, col in enumerate(columns):
            if col in header_map:
                table.setHorizontalHeaderItem(i, QTableWidgetItem(header_map[col]))
                
        table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            for col, key in enumerate(columns):
                value = item.get(key, "")
                if isinstance(value, float):
                    cell = QTableWidgetItem(f"{value:.2f}")
                elif isinstance(value, bool):
                    cell = QTableWidgetItem("Да" if value else "Нет")
                else:
                    cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col, cell)
                
        table.resizeColumnsToContents()