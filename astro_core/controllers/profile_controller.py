"""
Profile Controller - business logic for birth profile management.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import date, time
from pathlib import Path

from ..profiles import (
    save_profile,
    load_profile,
    list_profiles,
    delete_profile,
    profile_to_filename,
)
from ..paths import get_profiles_dir


@dataclass
class BirthProfile:
    name: str
    birth_date: date
    birth_time: time
    latitude: float
    longitude: float
    utc_offset_hours: float
    timezone: str = ""
    city_name: str = ""
    city_country: str = ""
    city_timezone: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileController:
    """Controller for birth profile operations."""

    def __init__(self, profiles_dir: Optional[str] = None):
        self._profiles_dir = profiles_dir or str(get_profiles_dir())
        self._current_profile: Optional[BirthProfile] = None
        self._editing_profile_name: Optional[str] = None

    def save_profile(self, profile: BirthProfile) -> Path:
        """Save a birth profile."""
        profile_data = {
            "name": profile.name,
            "date": profile.birth_date.strftime("%Y-%m-%d"),
            "time": profile.birth_time.strftime("%H:%M"),
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "utc_offset_hours": profile.utc_offset_hours,
            "timezone": profile.timezone,
            "city_name": profile.city_name,
            "city_country": profile.city_country,
            "city_timezone": profile.city_timezone,
        }
        return save_profile(profile_data, self._profiles_dir)

    def load_profile(self, name: str) -> BirthProfile:
        """Load a birth profile by name."""
        data = load_profile(name, self._profiles_dir)
        return self._dict_to_profile(data)

    def list_profiles(self) -> List[BirthProfile]:
        """List all saved profiles."""
        profiles_data = list_profiles(self._profiles_dir)
        return [self._dict_to_profile(p) for p in profiles_data]

    def delete_profile(self, name: str) -> bool:
        """Delete a profile by name."""
        return delete_profile(name, self._profiles_dir)

    def get_profile_names(self) -> List[str]:
        """Get list of profile names."""
        profiles = self.list_profiles()
        return [p.name for p in profiles]

    def set_current_profile(self, profile: BirthProfile):
        """Set the currently active profile."""
        self._current_profile = profile

    def get_current_profile(self) -> Optional[BirthProfile]:
        """Get the currently active profile."""
        return self._current_profile

    def set_editing_profile(self, name: Optional[str]):
        """Set the profile being edited."""
        self._editing_profile_name = name

    def get_editing_profile_name(self) -> Optional[str]:
        """Get the name of the profile being edited."""
        return self._editing_profile_name

    def clear_editing_profile(self):
        """Clear the editing profile state."""
        self._editing_profile_name = None

    def profile_to_birth_data(self, profile: BirthProfile) -> dict:
        """Convert BirthProfile to birth data dict for chart calculation."""
        return {
            "name": profile.name,
            "date": profile.birth_date.strftime("%Y-%m-%d"),
            "time": profile.birth_time.strftime("%H:%M"),
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "utc_offset_hours": profile.utc_offset_hours,
            "timezone": profile.timezone,
            "city_name": profile.city_name,
            "city_country": profile.city_country,
            "city_timezone": profile.city_timezone,
        }

    def _dict_to_profile(self, data: dict) -> BirthProfile:
        """Convert profile dict to BirthProfile dataclass."""
        birth_date = date.fromisoformat(data["date"]) if "date" in data else date.today()
        birth_time = time.fromisoformat(data["time"]) if "time" in data else time(0, 0)
        
        return BirthProfile(
            name=data.get("name", ""),
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=float(data.get("latitude", 0.0)),
            longitude=float(data.get("longitude", 0.0)),
            utc_offset_hours=float(data.get("utc_offset_hours", 0.0)),
            timezone=data.get("timezone", ""),
            city_name=data.get("city_name", ""),
            city_country=data.get("city_country", ""),
            city_timezone=data.get("city_timezone", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @staticmethod
    def validate_profile(profile: BirthProfile) -> list:
        """Validate profile data, return list of errors."""
        errors = []
        
        if not profile.name or not profile.name.strip():
            errors.append("Profile name is required")
            
        if profile.latitude < -90 or profile.latitude > 90:
            errors.append("Latitude must be between -90 and 90")
            
        if profile.longitude < -180 or profile.longitude > 180:
            errors.append("Longitude must be between -180 and 180")
            
        if profile.utc_offset_hours < -12 or profile.utc_offset_hours > 14:
            errors.append("UTC offset must be between -12 and +14")
            
        return errors