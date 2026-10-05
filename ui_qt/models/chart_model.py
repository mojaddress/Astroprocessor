"""
Chart Models - Table models for displaying chart data.
"""
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List, Dict, Any, Optional


class ChartTableModel(QAbstractTableModel):
    """Generic table model for chart data."""
    
    def __init__(self, data: List[Dict] = None, columns: List[str] = None, 
                 header_map: Dict[str, str] = None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._columns = columns or []
        self._header_map = header_map or {}
        
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)
        
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)
        
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
            
        row = index.row()
        col = index.column()
        
        if row >= len(self._data) or col >= len(self._columns):
            return None
            
        item = self._data[row]
        key = self._columns[col]
        value = item.get(key, "")
        
        if isinstance(value, float):
            return f"{value:.2f}"
        elif isinstance(value, bool):
            return "Да" if value else "Нет"
        return str(value)
        
    def headerData(self, section: int, orientation: Qt.Orientation, 
                   role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section < len(self._columns):
                key = self._columns[section]
                return self._header_map.get(key, key)
        return None
        
    def set_data(self, data: List[Dict], columns: List[str] = None):
        """Update model data."""
        self.beginResetModel()
        self._data = data or []
        if columns:
            self._columns = columns
        self.endResetModel()
        
    def get_data(self) -> List[Dict]:
        return self._data


# Predefined column configurations
OBJECT_COLUMNS = ["name", "longitude", "sign", "degree", "house", "retrograde", "speed"]
OBJECT_HEADERS = {
    "name": "Планета",
    "longitude": "Долгота",
    "sign": "Знак",
    "degree": "Градус",
    "house": "Дом",
    "retrograde": "Ретро",
    "speed": "Скорость",
}

HOUSE_COLUMNS = ["number", "longitude", "sign", "degree"]
HOUSE_HEADERS = {
    "number": "№",
    "longitude": "Долгота",
    "sign": "Знак",
    "degree": "Градус",
}

ASPECT_COLUMNS = ["planet1", "planet2", "aspect", "orb", "strength", "applying"]
ASPECT_HEADERS = {
    "planet1": "Планета 1",
    "planet2": "Планета 2",
    "aspect": "Аспект",
    "orb": "Орб",
    "strength": "Сила",
    "applying": "Сходится",
}

TRANSIT_CALENDAR_COLUMNS = ["date", "transit_planet", "aspect", "natal_point", "orb", "strength"]
TRANSIT_CALENDAR_HEADERS = {
    "date": "Дата",
    "transit_planet": "Транзитная планета",
    "aspect": "Аспект",
    "natal_point": "Натальная точка",
    "orb": "Орб",
    "strength": "Сила",
}

TRANSIT_PRECISE_COLUMNS = ["exact_datetime", "direction", "transit_planet", "aspect", "natal_point", "orb"]
TRANSIT_PRECISE_HEADERS = {
    "exact_datetime": "Точное время",
    "direction": "Напр.",
    "transit_planet": "Транзитная планета",
    "aspect": "Аспект",
    "natal_point": "Натальная точка",
    "orb": "Орб",
}

TRANSIT_PERIODS_COLUMNS = ["transit_planet", "aspect", "natal_point", "start_date", "exact_date", "end_date", "orb", "strength"]
TRANSIT_PERIODS_HEADERS = {
    "transit_planet": "Транзитная планета",
    "aspect": "Аспект",
    "natal_point": "Натальная точка",
    "start_date": "Вход в орб",
    "exact_date": "Пик",
    "end_date": "Выход из орба",
    "orb": "Орб",
    "strength": "Сила",
}

PROGRESSION_PLANET_COLUMNS = ["name", "longitude", "sign", "degree", "speed", "retrograde"]
PROGRESSION_PLANET_HEADERS = {
    "name": "Планета",
    "longitude": "Долгота",
    "sign": "Знак",
    "degree": "Градус",
    "speed": "Скорость",
    "retrograde": "Ретро",
}

PROGRESSION_ASPECT_COLUMNS = ["progressed_planet", "aspect", "natal_point", "orb", "strength", "applying"]
PROGRESSION_ASPECT_HEADERS = {
    "progressed_planet": "Прогрессивная планета",
    "aspect": "Аспект",
    "natal_point": "Натальная точка",
    "orb": "Орб",
    "strength": "Сила",
    "applying": "Сходится",
}


def create_model_for_objects(data: List[Dict]) -> ChartTableModel:
    """Create model for natal chart objects."""
    return ChartTableModel(data, OBJECT_COLUMNS, OBJECT_HEADERS)


def create_model_for_houses(data: List[Dict]) -> ChartTableModel:
    """Create model for houses."""
    return ChartTableModel(data, HOUSE_COLUMNS, HOUSE_HEADERS)


def create_model_for_aspects(data: List[Dict]) -> ChartTableModel:
    """Create model for aspects."""
    return ChartTableModel(data, ASPECT_COLUMNS, ASPECT_HEADERS)


def create_model_for_transit_calendar(data: List[Dict]) -> ChartTableModel:
    """Create model for transit calendar."""
    return ChartTableModel(data, TRANSIT_CALENDAR_COLUMNS, TRANSIT_CALENDAR_HEADERS)


def create_model_for_transit_precise(data: List[Dict]) -> ChartTableModel:
    """Create model for precise transits."""
    return ChartTableModel(data, TRANSIT_PRECISE_COLUMNS, TRANSIT_PRECISE_HEADERS)


def create_model_for_transit_periods(data: List[Dict]) -> ChartTableModel:
    """Create model for transit periods."""
    return ChartTableModel(data, TRANSIT_PERIODS_COLUMNS, TRANSIT_PERIODS_HEADERS)


def create_model_for_progression_planets(data: List[Dict]) -> ChartTableModel:
    """Create model for progression planets."""
    return ChartTableModel(data, PROGRESSION_PLANET_COLUMNS, PROGRESSION_PLANET_HEADERS)


def create_model_for_progression_aspects(data: List[Dict]) -> ChartTableModel:
    """Create model for progression aspects."""
    return ChartTableModel(data, PROGRESSION_ASPECT_COLUMNS, PROGRESSION_ASPECT_HEADERS)