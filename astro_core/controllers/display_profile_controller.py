"""
Display Profile Controller - business logic for display profile management.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from ..display_profiles import (
    load_display_profile,
    save_display_profile,
    list_display_profiles,
    delete_display_profile,
    validate_profile,
    get_render_kwargs,
    get_appearance,
    apply_profile_to_settings,
    get_builtin_profiles,
    ALL_PLANETS,
    ALL_ASPECTS,
    DEFAULT_ORBS,
    DEFAULT_DISPLAY_PROFILES_DIR,
)


@dataclass
class DisplayProfile:
    name: str
    description: str = ""
    objects: Optional[Dict[str, bool]] = None
    aspects: Optional[Dict[str, Dict[str, Any]]] = None
    appearance: Optional[Dict[str, Any]] = None
    _builtin: bool = False
    _filename: Optional[str] = None


class DisplayProfileController:
    """Controller for display profile operations."""

    def __init__(self, profiles_dir: Optional[str] = None):
        self._profiles_dir = profiles_dir or DEFAULT_DISPLAY_PROFILES_DIR
        self._current_profile_name: str = "full"
        self._current_profile: Optional[DisplayProfile] = None

    def load_profile(self, name: str) -> DisplayProfile:
        """Load a display profile by name."""
        data = load_display_profile(name, self._profiles_dir)
        profile = self._dict_to_profile(data)
        self._current_profile_name = name
        self._current_profile = profile
        return profile

    def save_profile(self, profile: DisplayProfile) -> str:
        """Save a display profile."""
        # Convert to dict format for saving
        data = self._profile_to_dict(profile)
        file_path = save_display_profile(data, self._profiles_dir)
        self._current_profile_name = profile.name
        self._current_profile = profile
        return str(file_path)

    def list_profiles(self) -> List[DisplayProfile]:
        """List all display profiles (builtin + user)."""
        profiles_data = list_display_profiles(self._profiles_dir)
        return [self._dict_to_profile(p) for p in profiles_data]

    def get_profile_names(self) -> List[str]:
        """Get list of profile names."""
        return [p.name for p in self.list_profiles()]

    def delete_profile(self, name: str) -> bool:
        """Delete a user display profile."""
        return delete_display_profile(name, self._profiles_dir)

    def get_current_profile(self) -> Optional[DisplayProfile]:
        """Get the currently active display profile."""
        if self._current_profile is None:
            self._current_profile = self.load_profile(self._current_profile_name)
        return self._current_profile

    def get_current_profile_name(self) -> str:
        """Get the name of the currently active profile."""
        return self._current_profile_name

    def set_current_profile(self, name: str):
        """Set the current profile by name."""
        self.load_profile(name)

    def apply_to_settings(self, base_settings: Optional[dict] = None) -> dict:
        """Apply current profile to calculation settings."""
        profile = self.get_current_profile()
        if profile:
            data = self._profile_to_dict(profile)
            return apply_profile_to_settings(data, base_settings)
        return base_settings or {}

    def get_render_kwargs(self) -> dict:
        """Get rendering kwargs for chart_svg from current profile."""
        profile = self.get_current_profile()
        if profile:
            data = self._profile_to_dict(profile)
            return get_render_kwargs(data)
        return {}

    def get_appearance_settings(self) -> dict:
        """Get appearance settings from current profile."""
        profile = self.get_current_profile()
        if profile:
            data = self._profile_to_dict(profile)
            return get_appearance(data)
        return {}

    def validate_profile(self, profile: DisplayProfile) -> List[str]:
        """Validate a display profile."""
        data = self._profile_to_dict(profile)
        return validate_profile(data)

    def get_builtin_profiles(self) -> Dict[str, DisplayProfile]:
        """Get builtin profiles."""
        builtin = get_builtin_profiles()
        return {name: self._dict_to_profile(data) for name, data in builtin.items()}

    def create_default_profile(self, name: str) -> DisplayProfile:
        """Create a new profile with default settings."""
        return DisplayProfile(
            name=name,
            description="User display profile",
            objects={p: True for p in ALL_PLANETS} | {
                "Chiron": True, "LunarNodes": True, "PartOfFortune": True, "Angles": True
            },
            aspects={a: {"enabled": True, "orb": DEFAULT_ORBS[a]} for a in ALL_ASPECTS},
            appearance={
                "label_mode": "symbols",
                "show_houses": True,
                "show_aspect_lines": True,
                "chart_size": 800,
                "planet_dot_size": 5,
                "planet_colors": {},
                "aspect_colors": {},
            },
        )

    def _dict_to_profile(self, data: dict) -> DisplayProfile:
        """Convert dict to DisplayProfile dataclass."""
        return DisplayProfile(
            name=data.get("name", ""),
            description=data.get("description", ""),
            objects=data.get("objects"),
            aspects=data.get("aspects"),
            appearance=data.get("appearance"),
            _builtin=data.get("_builtin", False),
            _filename=data.get("_filename"),
        )

    def _profile_to_dict(self, profile: DisplayProfile) -> dict:
        """Convert DisplayProfile to dict for saving."""
        return {
            "name": profile.name,
            "description": profile.description,
            "objects": profile.objects,
            "aspects": profile.aspects,
            "appearance": profile.appearance,
        }