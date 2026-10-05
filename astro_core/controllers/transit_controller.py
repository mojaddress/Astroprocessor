"""
Transit Controller - business logic for transit calculations.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import date

from ..transits import (
    get_transit_calendar,
    find_transit_events,
    find_transit_periods,
    calculate_transit_positions,
    find_transits_on_date,
)
from ..chart import build_natal_chart
from ..display_profiles import apply_profile_to_settings, load_display_profile


TransitMode = Literal["calendar", "precise", "periods"]


@dataclass
class TransitSettings:
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
    transit_utc_offset: float = 0.0
    transit_planets: Optional[list] = None


@dataclass
class TransitPeriod:
    start_date: str
    end_date: str


class TransitController:
    """Controller for transit operations."""

    def __init__(self):
        self._last_result = None
        self._last_mode: Optional[TransitMode] = None
        self._last_period: Optional[TransitPeriod] = None

    def calculate_transits(
        self,
        natal_objects: list,
        start_date: str,
        end_date: str,
        settings: TransitSettings,
        mode: TransitMode = "calendar",
        filter_planets: Optional[list] = None,
        filter_aspects: Optional[list] = None,
        display_profile_name: Optional[str] = None,
    ) -> list:
        """
        Calculate transits for a period.
        
        Args:
            natal_objects: Natal chart objects
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            settings: Transit settings
            mode: Calculation mode (calendar, precise, periods)
            filter_planets: Filter by transit planets
            filter_aspects: Filter by aspects
            display_profile_name: Optional display profile
            
        Returns:
            List of transit events/calendar entries/periods
        """
        transit_settings = self._settings_to_dict(settings)
        
        if display_profile_name:
            try:
                profile = load_display_profile(display_profile_name)
                transit_settings = apply_profile_to_settings(profile, transit_settings)
            except FileNotFoundError:
                pass

        # Apply transit_planets from profile (enabled_planets -> transit_planets mapping)
        if "enabled_planets" in transit_settings and transit_settings["enabled_planets"]:
            transit_settings["transit_planets"] = list(transit_settings["enabled_planets"])

        filter_p = filter_planets if filter_planets else None
        filter_a = filter_aspects if filter_aspects else None

        if mode == "periods":
            result = find_transit_periods(
                natal_objects, start_date, end_date, transit_settings,
                filter_planets=filter_p, filter_aspects=filter_a
            )
        elif mode == "precise":
            result = find_transit_events(
                natal_objects, start_date, end_date, transit_settings,
                filter_planets=filter_p, filter_aspects=filter_a
            )
        else:
            result = get_transit_calendar(
                natal_objects, start_date, end_date, transit_settings,
                filter_planets=filter_p, filter_aspects=filter_a
            )

        self._last_result = result
        self._last_mode = mode
        self._last_period = TransitPeriod(start_date=start_date, end_date=end_date)
        
        return result

    def calculate_single_date_transits(
        self,
        natal_objects: list,
        transit_date: str,
        settings: TransitSettings,
        filter_planets: Optional[list] = None,
        filter_aspects: Optional[list] = None,
    ) -> list:
        """Calculate transits for a single date (calendar mode)."""
        return self.calculate_transits(
            natal_objects, transit_date, transit_date, settings,
            mode="calendar", filter_planets=filter_planets, filter_aspects=filter_aspects
        )

    def calculate_transit_chart_data(
        self,
        natal_chart_result: dict,
        transit_date: date,
        transit_city: Optional[dict],
        natal_utc_offset: float,
        selected_planets: Optional[list] = None,
        selected_aspects: Optional[list] = None,
    ) -> dict:
        """
        Calculate data needed for transit chart SVG rendering.
        Returns transit planets, aspects, houses, and additional points.
        """
        from ..time_service import datetime_to_jd
        from datetime import datetime, time, timedelta

        transit_dt = datetime.combine(transit_date, time(12, 0))
        transit_utc_dt = transit_dt - timedelta(hours=natal_utc_offset)
        transit_jd = datetime_to_jd(transit_utc_dt)

        transit_settings = {"include_chiron": False, "include_nodes": False}
        transit_planets_list, _ = calculate_transit_positions(transit_jd, transit_settings)

        if selected_planets:
            transit_planets_list = [p for p in transit_planets_list if p["name"] in selected_planets]

        transit_chart_settings = dict(natal_chart_result.get("settings", {}))
        if selected_aspects:
            transit_chart_settings["enabled_aspects"] = list(selected_aspects)

        natal_objects = natal_chart_result.get("objects", [])
        transit_aspects_list = find_transits_on_date(natal_objects, transit_planets_list, transit_chart_settings)

        transit_houses = None
        transit_additional_points = None

        if transit_city is not None:
            from ..timezone_service import get_utc_offset_hours
            try:
                transit_tz_name = transit_city.get("timezone", "")
                if transit_tz_name:
                    transit_utc_offset_hours = get_utc_offset_hours(transit_tz_name, transit_dt)
                else:
                    transit_utc_offset_hours = 0.0

                natal_settings_for_ephe = natal_chart_result.get("settings", {})
                transit_ephe_path = natal_settings_for_ephe.get("ephe_path", "ephe")

                transit_chart_birth = {
                    "name": "Transit",
                    "date": transit_date.strftime("%Y-%m-%d"),
                    "time": "12:00",
                    "latitude": transit_city["latitude"],
                    "longitude": transit_city["longitude"],
                    "utc_offset_hours": transit_utc_offset_hours,
                }

                transit_chart_settings = {
                    "include_chiron": False,
                    "include_nodes": False,
                    "include_part_of_fortune": False,
                    "include_angles": True,
                    "ephe_path": transit_ephe_path,
                }

                transit_chart_result = build_natal_chart(transit_chart_birth, transit_chart_settings)
                transit_houses = transit_chart_result.get("houses", [])
                transit_additional_points = transit_chart_result.get("additional_points", [])
            except Exception:
                pass  # Silently fail, will render without transit houses

        return {
            "transit_planets": transit_planets_list,
            "transit_aspects": transit_aspects_list,
            "transit_houses": transit_houses,
            "transit_additional_points": transit_additional_points,
        }

    def get_last_result(self):
        return self._last_result

    def get_last_mode(self) -> Optional[TransitMode]:
        return self._last_mode

    def get_last_period(self) -> Optional[TransitPeriod]:
        return self._last_period

    def _settings_to_dict(self, settings: TransitSettings) -> dict:
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
            "transit_utc_offset": settings.transit_utc_offset,
            "transit_planets": settings.transit_planets,
        }

    @staticmethod
    def get_default_settings() -> TransitSettings:
        return TransitSettings()