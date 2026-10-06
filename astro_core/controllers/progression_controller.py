"""
Progression Controller - business logic for progression calculations.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import date

from ..progressions import (
    calculate_secondary_progressions,
    calculate_solar_arc_progressions,
    find_progression_aspects,
)
from ..chart import build_natal_chart
from ..display_profiles import apply_profile_to_settings, load_display_profile


ProgressionType = Literal["secondary", "solar_arc"]


@dataclass
class ProgressionSettings:
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


@dataclass
class ProgressionResult:
    progressed_planets: list
    progressed_points: list
    aspects: list
    progression_type: ProgressionType
    progression_date: str
    age_years: float


class ProgressionController:
    """Controller for progression operations."""

    def __init__(self):
        self._last_result: Optional[ProgressionResult] = None

    def calculate_progressions(
        self,
        birth_data: dict,
        progression_date: date,
        progression_type: ProgressionType = "secondary",
        settings: Optional[ProgressionSettings] = None,
        display_profile_name: Optional[str] = None,
    ) -> ProgressionResult:
        """
        Calculate progressions for a given date.
        
        Args:
            birth_data: Birth data dictionary
            progression_date: Date for progression calculation
            progression_type: Type of progression (secondary or solar_arc)
            settings: Calculation settings
            display_profile_name: Optional display profile
            
        Returns:
            ProgressionResult with progressed planets, points, and aspects
        """
        if settings is None:
            settings = ProgressionSettings()

        settings_dict = self._settings_to_dict(settings)
        
        if display_profile_name:
            try:
                profile = load_display_profile(display_profile_name)
                settings_dict = apply_profile_to_settings(profile, settings_dict)
            except FileNotFoundError:
                pass

        # Build natal chart first
        natal_chart = build_natal_chart(birth_data, settings_dict)
        natal_objects = natal_chart.get("objects", [])

        # Calculate progressions
        if progression_type == "secondary":
            progressed_result = calculate_secondary_progressions(
                birth_data, progression_date, settings_dict
            )
            progressed_planets = progressed_result.get("planets", [])
        else:
            progressed_result = calculate_solar_arc_progressions(
                birth_data, progression_date, settings_dict
            )
            progressed_planets = progressed_result.get("planets", [])

        # Calculate progressed houses and angles (ASC, MC)
        # We use build_natal_chart with the progressed date
        progressed_birth = dict(birth_data)
        progressed_birth["date"] = progression_date.strftime("%Y-%m-%d")
        progressed_birth["time"] = "12:00"  # Progressed charts typically use noon
        
        progressed_chart = build_natal_chart(progressed_birth, settings_dict)
        progressed_points = progressed_chart.get("additional_points", [])
        progressed_houses = progressed_chart.get("houses", [])

        # Find aspects between progressed and natal
        aspects = find_progression_aspects(progressed_planets, natal_objects, settings_dict)

        # Calculate age
        from datetime import datetime
        birth_dt = datetime.strptime(birth_data["date"], "%Y-%m-%d")
        prog_dt = datetime.combine(progression_date, datetime.min.time())
        age_years = (prog_dt - birth_dt).days / 365.25

        result = ProgressionResult(
            progressed_planets=progressed_planets,
            progressed_points=progressed_points,
            aspects=aspects,
            progression_type=progression_type,
            progression_date=progression_date.strftime("%Y-%m-%d"),
            age_years=age_years,
        )

        self._last_result = result
        return result

    def get_last_result(self) -> Optional[ProgressionResult]:
        return self._last_result

    def _settings_to_dict(self, settings: ProgressionSettings) -> dict:
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
    def get_default_settings() -> ProgressionSettings:
        return ProgressionSettings()