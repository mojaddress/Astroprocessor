"""
Settings Manager - manages application settings and preferences.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path
import json


@dataclass
class AppSettings:
    """Application settings that persist between sessions."""
    
    # General
    language: str = "ru"
    theme: str = "light"  # light, dark, auto
    
    # Calculation defaults
    default_house_system: str = "placidus"
    default_zodiac: str = "tropical"
    default_ayanamsha: str = "lahiri"
    default_include_chiron: bool = True
    default_include_nodes: bool = True
    default_include_fortune: bool = True
    default_include_angles: bool = True
    default_ephe_path: str = "ephe"
    
    # Display defaults
    default_display_profile: str = "full"
    default_chart_size: int = 800
    default_dot_size: int = 5
    default_label_mode: str = "symbols"
    default_show_aspects: bool = True
    default_show_houses: bool = True
    
    # Transit defaults
    default_transit_mode: str = "calendar"  # calendar, precise, periods
    default_transit_days: int = 7
    default_transit_utc_offset: float = 0.0
    
    # Progression defaults
    default_progression_type: str = "secondary"  # secondary, solar_arc
    
    # UI preferences
    auto_recalculate: bool = True
    show_warnings: bool = True
    compact_mode: bool = False
    
    # Paths
    profiles_dir: str = "profiles"
    display_profiles_dir: str = "config/display_profiles"
    cities_file: str = "data/cities.json"
    ephe_dir: str = "ephe"
    
    # Advanced
    log_level: str = "INFO"
    max_transit_days_precise: int = 60
    max_transit_days_periods: int = 365


class SettingsManager:
    """Manages application settings persistence."""
    
    def __init__(self, settings_file: Optional[Path] = None):
        self._settings_file = settings_file or Path("config/user_settings.json")
        self._settings = AppSettings()
        self._load()
    
    @property
    def settings(self) -> AppSettings:
        return self._settings
    
    def _load(self):
        """Load settings from file."""
        if self._settings_file.exists():
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Update only known fields
                for key, value in data.items():
                    if hasattr(self._settings, key):
                        setattr(self._settings, key, value)
            except Exception:
                pass  # Use defaults on error
    
    def save(self):
        """Save settings to file."""
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self._settings), f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Silently fail
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = AppSettings()
        self.save()
    
    def update(self, **kwargs):
        """Update multiple settings at once."""
        for key, value in kwargs.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
        self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return getattr(self._settings, key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value."""
        if hasattr(self._settings, key):
            setattr(self._settings, key, value)
            self.save()