"""
City Controller - business logic for city search and timezone management.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from ..cities import load_cities, search_cities, get_city_by_name, get_city_display_name
from ..timezone_service import get_utc_offset_hours, get_timezone_info


@dataclass
class City:
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    display_name: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = get_city_display_name(self.__dict__)


class CityController:
    """Controller for city and timezone operations."""

    def __init__(self):
        self._cached_cities: Optional[List[City]] = None

    def search_cities(self, query: str, limit: int = 10) -> List[City]:
        """Search cities by name."""
        if not query or not query.strip():
            return self.get_all_cities()[:limit]
        
        results = search_cities(query.strip(), limit=limit)
        return [self._dict_to_city(c) for c in results]

    def get_all_cities(self) -> List[City]:
        """Get all cities from database."""
        if self._cached_cities is None:
            cities_data = load_cities()
            self._cached_cities = [self._dict_to_city(c) for c in cities_data]
        return self._cached_cities

    def get_city_by_name(self, name: str) -> Optional[City]:
        """Get city by exact name match."""
        data = get_city_by_name(name)
        if data:
            return self._dict_to_city(data)
        return None

    def get_city_display_name(self, city: City) -> str:
        """Get formatted display name for a city."""
        return city.display_name

    def get_utc_offset(self, city: City, dt: datetime) -> float:
        """Get UTC offset for a city at a specific datetime."""
        if city.timezone:
            try:
                return get_utc_offset_hours(city.timezone, dt)
            except ValueError:
                return 0.0
        return 0.0

    def get_timezone_info(self, city: City, dt: datetime) -> dict:
        """Get detailed timezone info for a city at a specific datetime."""
        if city.timezone:
            try:
                return get_timezone_info(city.timezone, dt)
            except ValueError:
                return {"utc_offset": 0.0, "is_dst": False, "abbreviation": "UTC"}
        return {"utc_offset": 0.0, "is_dst": False, "abbreviation": "UTC"}

    def clear_cache(self):
        """Clear the cities cache."""
        self._cached_cities = None

    def _dict_to_city(self, data: dict) -> City:
        """Convert city dict to City dataclass."""
        return City(
            name=data.get("name", ""),
            country=data.get("country", ""),
            latitude=float(data.get("latitude", 0.0)),
            longitude=float(data.get("longitude", 0.0)),
            timezone=data.get("timezone", ""),
        )