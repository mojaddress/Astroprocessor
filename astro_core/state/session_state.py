"""
State Management - unified session state for the application.
Pure Python, no Streamlit/UI dependencies.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import date, time
from pathlib import Path

from ..controllers.chart_controller import BirthData, ChartSettings
from ..controllers.transit_controller import TransitSettings, TransitMode, TransitPeriod
from ..controllers.progression_controller import ProgressionSettings, ProgressionType, ProgressionResult
from ..controllers.profile_controller import BirthProfile
from ..controllers.display_profile_controller import DisplayProfile
from ..controllers.city_controller import City


@dataclass
class AppState:
    """Complete application state."""
    
    # UI state
    show_left_panel: bool = True
    show_right_panel: bool = True
    current_tab: str = "chart"  # chart, transits, progressions
    
    # Birth data
    birth_data: Optional[BirthData] = None
    chart_settings: ChartSettings = field(default_factory=ChartSettings)
    
    # Chart result
    chart_result: Optional[Dict[str, Any]] = None
    chart_last_calculated: Optional[str] = None
    
    # Display profile
    display_profile_name: str = "full"
    display_profile: Optional[DisplayProfile] = None
    
    # Transit state
    transit_mode: TransitMode = "calendar"
    transit_start_date: date = field(default_factory=date.today)
    transit_end_date: date = field(default_factory=lambda: date.today())
    transit_settings: TransitSettings = field(default_factory=TransitSettings)
    transit_filter_planets: List[str] = field(default_factory=list)
    transit_filter_aspects: List[str] = field(default_factory=list)
    transit_result: Optional[List[Dict[str, Any]]] = None
    transit_mode_used: Optional[TransitMode] = None
    transit_period: Optional[TransitPeriod] = None
    transit_city: Optional[City] = None
    transit_location_mode: str = "none"  # none, city
    current_transit_date: date = field(default_factory=date.today)
    
    # Progression state
    progression_type: ProgressionType = "secondary"
    progression_date: date = field(default_factory=date.today)
    progression_settings: ProgressionSettings = field(default_factory=ProgressionSettings)
    progression_result: Optional[ProgressionResult] = None
    
    # Profile state
    current_profile: Optional[BirthProfile] = None
    editing_profile_name: Optional[str] = None
    profiles_list: List[BirthProfile] = field(default_factory=list)
    
    # Display profile editor state
    sel_planets: List[str] = field(default_factory=list)
    sel_aspects: List[str] = field(default_factory=list)
    orb_values: Dict[str, float] = field(default_factory=dict)
    aspect_colors: Dict[str, str] = field(default_factory=dict)
    planet_colors: Dict[str, str] = field(default_factory=dict)
    label_mode: str = "symbols"
    show_aspects: bool = True
    show_houses: bool = True
    chart_size: int = 800
    dot_size: int = 5
    chk_chiron: bool = True
    chk_nodes: bool = True
    chk_fortune: bool = True
    chk_angles: bool = True
    
    # Chart display
    chart_type: str = "Натальная карта"  # Натальная карта, Транзитная карта
    chart_size_ui: int = 800
    
    # Additional state fields (for UI compatibility)
    flag_recalculate_chart: bool = False
    display_profile_error: Optional[str] = None
    display_profile_selector: str = "full"
    sel_display_profile_name: str = "full"
    birth: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    
    # Validation errors
    last_error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary (for persistence)."""
        return {
            "show_left_panel": self.show_left_panel,
            "show_right_panel": self.show_right_panel,
            "current_tab": self.current_tab,
            "display_profile_name": self.display_profile_name,
            "transit_mode": self.transit_mode,
            "transit_start_date": self.transit_start_date.isoformat() if self.transit_start_date else None,
            "transit_end_date": self.transit_end_date.isoformat() if self.transit_end_date else None,
            "transit_filter_planets": self.transit_filter_planets,
            "transit_filter_aspects": self.transit_filter_aspects,
            "transit_location_mode": self.transit_location_mode,
            "current_transit_date": self.current_transit_date.isoformat() if self.current_transit_date else None,
            "progression_type": self.progression_type,
            "progression_date": self.progression_date.isoformat() if self.progression_date else None,
            "chart_type": self.chart_type,
            "chart_size_ui": self.chart_size_ui,
            "sel_planets": self.sel_planets,
            "sel_aspects": self.sel_aspects,
            "orb_values": self.orb_values,
            "aspect_colors": self.aspect_colors,
            "planet_colors": self.planet_colors,
            "label_mode": self.label_mode,
            "show_aspects": self.show_aspects,
            "show_houses": self.show_houses,
            "chart_size": self.chart_size,
            "dot_size": self.dot_size,
            "chk_chiron": self.chk_chiron,
            "chk_nodes": self.chk_nodes,
            "chk_fortune": self.chk_fortune,
            "chk_angles": self.chk_angles,
            "flag_recalculate_chart": self.flag_recalculate_chart,
            "display_profile_error": self.display_profile_error,
            "display_profile_selector": self.display_profile_selector,
            "sel_display_profile_name": self.sel_display_profile_name,
            "birth": self.birth,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppState":
        """Deserialize state from dictionary."""
        state = cls()
        
        state.show_left_panel = data.get("show_left_panel", True)
        state.show_right_panel = data.get("show_right_panel", True)
        state.current_tab = data.get("current_tab", "chart")
        state.display_profile_name = data.get("display_profile_name", "full")
        state.transit_mode = data.get("transit_mode", "calendar")
        
        if data.get("transit_start_date"):
            state.transit_start_date = date.fromisoformat(data["transit_start_date"])
        if data.get("transit_end_date"):
            state.transit_end_date = date.fromisoformat(data["transit_end_date"])
            
        state.transit_filter_planets = data.get("transit_filter_planets", [])
        state.transit_filter_aspects = data.get("transit_filter_aspects", [])
        state.transit_location_mode = data.get("transit_location_mode", "none")
        
        if data.get("current_transit_date"):
            state.current_transit_date = date.fromisoformat(data["current_transit_date"])
            
        state.progression_type = data.get("progression_type", "secondary")
        if data.get("progression_date"):
            state.progression_date = date.fromisoformat(data["progression_date"])
            
        state.chart_type = data.get("chart_type", "Натальная карта")
        state.chart_size_ui = data.get("chart_size_ui", 800)
        state.sel_planets = data.get("sel_planets", [])
        state.sel_aspects = data.get("sel_aspects", [])
        state.orb_values = data.get("orb_values", {})
        state.aspect_colors = data.get("aspect_colors", {})
        state.planet_colors = data.get("planet_colors", {})
        state.label_mode = data.get("label_mode", "symbols")
        state.show_aspects = data.get("show_aspects", True)
        state.show_houses = data.get("show_houses", True)
        state.chart_size = data.get("chart_size", 800)
        state.dot_size = data.get("dot_size", 5)
        state.chk_chiron = data.get("chk_chiron", True)
        state.chk_nodes = data.get("chk_nodes", True)
        state.chk_fortune = data.get("chk_fortune", True)
        state.chk_angles = data.get("chk_angles", True)
        
        state.flag_recalculate_chart = data.get("flag_recalculate_chart", False)
        state.display_profile_error = data.get("display_profile_error")
        state.display_profile_selector = data.get("display_profile_selector", "full")
        state.sel_display_profile_name = data.get("sel_display_profile_name", "full")
        state.birth = data.get("birth")
        state.settings = data.get("settings")
        
        return state

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like get access for compatibility."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Dictionary-like access for compatibility."""
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any):
        """Dictionary-like set for compatibility."""
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        """Check if attribute exists."""
        return hasattr(self, key)


class StateManager:
    """Manages application state persistence."""
    
    def __init__(self, state_file: Optional[Path] = None):
        self._state = AppState()
        self._state_file = state_file
        self._dirty = False
    
    @property
    def state(self) -> AppState:
        return self._state
    
    def mark_dirty(self):
        self._dirty = True
    
    def save(self):
        """Save state to file."""
        if self._state_file and self._dirty:
            import json
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(self._state.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self._dirty = False
    
    def load(self):
        """Load state from file."""
        if self._state_file and self._state_file.exists():
            import json
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            self._state = AppState.from_dict(data)
            self._dirty = False
    
    def reset(self):
        """Reset to default state."""
        self._state = AppState()
        self._dirty = True