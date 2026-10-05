"""
Chart Controller - business logic for natal chart calculations.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, time

from ..chart import build_natal_chart
from ..display_profiles import apply_profile_to_settings, load_display_profile, list_display_profiles
from ..constants import DEFAULT_SETTINGS


@dataclass
class BirthData:
    name: str
    birth_date: date
    birth_time: time
    latitude: float
    longitude: float
    utc_offset_hours: float
    coord_source: str = "manual"
    timezone: str = ""


@dataclass
class ChartSettings:
    house_system: str = "placidus"
    zodiac: str = "tropical"
    ayanamsha: str = "lahiri"
    include_chiron: bool = True
    include_nodes: bool = True
    include_part_of_fortune: bool = True
    include_angles: bool = True
    ephe_path: Optional[str] = None
    enabled_planets: Optional[list] = None
    enabled_aspects: Optional[list] = None
    orbs: Optional[dict] = None


class ChartController:
    """Controller for natal chart operations."""

    def __init__(self):
        self._last_result = None
        self._last_birth = None
        self._last_settings = None

    def calculate_chart(self, birth: BirthData, settings: ChartSettings, display_profile_name: Optional[str] = None) -> dict:
        """
        Calculate natal chart with given birth data and settings.
        
        Args:
            birth: Birth data
            settings: Chart calculation settings
            display_profile_name: Optional display profile to apply
            
        Returns:
            Chart result dictionary
        """
        birth_dict = {
            "name": birth.name,
            "date": birth.birth_date.strftime("%Y-%m-%d"),
            "time": birth.birth_time.strftime("%H:%M"),
            "latitude": birth.latitude,
            "longitude": birth.longitude,
            "utc_offset_hours": birth.utc_offset_hours,
        }

        settings_dict = self._settings_to_dict(settings)
        
        if display_profile_name:
            try:
                profile = load_display_profile(display_profile_name)
                settings_dict = apply_profile_to_settings(profile, settings_dict)
            except FileNotFoundError:
                pass  # Use settings as-is

        result = build_natal_chart(birth_dict, settings_dict)
        
        self._last_result = result
        self._last_birth = birth_dict
        self._last_settings = settings_dict
        
        return result

    def get_last_result(self) -> Optional[dict]:
        return self._last_result

    def get_last_birth(self) -> Optional[dict]:
        return self._last_birth

    def get_last_settings(self) -> Optional[dict]:
        return self._last_settings

    def _settings_to_dict(self, settings: ChartSettings) -> dict:
        return {
            "house_system": settings.house_system,
            "zodiac": settings.zodiac,
            "ayanamsha": settings.ayanamsha,
            "include_chiron": settings.include_chiron,
            "include_nodes": settings.include_nodes,
            "include_part_of_fortune": settings.include_part_of_fortune,
            "include_angles": settings.include_angles,
            "ephe_path": settings.ephe_path,
            "enabled_planets": settings.enabled_planets,
            "enabled_aspects": settings.enabled_aspects,
            "orbs": settings.orbs,
        }

    @staticmethod
    def get_default_settings() -> ChartSettings:
        return ChartSettings()

    @staticmethod
    def get_available_display_profiles() -> list:
        return list_display_profiles()

    @staticmethod
    def validate_birth_data(birth: BirthData) -> list:
        """Validate birth data, return list of error messages."""
        errors = []
        
        if not birth.name or not birth.name.strip():
            errors.append("Name is required")
            
        if birth.latitude < -90 or birth.latitude > 90:
            errors.append("Latitude must be between -90 and 90")
            
        if birth.longitude < -180 or birth.longitude > 180:
            errors.append("Longitude must be between -180 and 180")
            
        if birth.utc_offset_hours < -12 or birth.utc_offset_hours > 14:
            errors.append("UTC offset must be between -12 and +14")
            
        if birth.birth_date > date.today():
            errors.append("Birth date cannot be in the future")
            
        return errors