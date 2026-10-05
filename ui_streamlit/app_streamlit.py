"""
Main Streamlit Application - new architecture entry point.
"""
import streamlit as st
from datetime import date, time
from pathlib import Path

from astro_core.ephemeris import SWISSEPH_AVAILABLE
from astro_core.controllers import (
    ChartController,
    TransitController,
    ProgressionController,
    DisplayProfileController,
    CityController,
    ProfileController,
)
from astro_core.state import AppState, StateManager, SettingsManager
from ui_streamlit.pages.chart_page import render_chart_page


# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(page_title="Astro Processor", page_icon="🌟", layout="wide")

# Compact styles
st.markdown(
    """
    <style>
    .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; }
    h1 { font-size: 1.6rem !important; line-height: 1.3 !important; margin-top: 0 !important; padding-top: 0 !important; }
    .stButton > button, .stDownloadButton > button {
        font-size: 0.78rem; padding: 0.3rem 0.5rem; height: auto; line-height: 1.2;
    }
    .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input, .stSelectbox select {
        font-size: 0.82rem;
    }
    label { font-size: 0.8rem; }
    div[data-testid="column"] { padding: 0 !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.35rem; }
    div[data-testid="stExpander"] { margin-bottom: 0.2rem; }
    .stCheckbox { min-height: 1.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Check Swiss Ephemeris
if not SWISSEPH_AVAILABLE:
    st.error("Swiss Ephemeris is not installed. Please install it with: `py -3.11 -m pip install pyswisseph`")
    st.stop()


# ============================================================
# Initialize Controllers and State
# ============================================================
@st.cache_resource
def get_controllers():
    """Initialize and cache controllers."""
    return {
        "chart": ChartController(),
        "transit": TransitController(),
        "progression": ProgressionController(),
        "display_profile": DisplayProfileController(),
        "city": CityController(),
        "profile": ProfileController(),
    }

@st.cache_resource
def get_state_manager():
    """Initialize state manager."""
    state_file = Path("config/app_state.json")
    return StateManager(state_file)

@st.cache_resource
def get_settings_manager():
    """Initialize settings manager."""
    settings_file = Path("config/user_settings.json")
    return SettingsManager(settings_file)


controllers = get_controllers()
state_manager = get_state_manager()
settings_manager = get_settings_manager()

# Load persisted state on first run
if "app_state_loaded" not in st.session_state:
    state_manager.load()
    st.session_state["app_state"] = state_manager.state
    st.session_state["app_state_loaded"] = True

state = st.session_state["app_state"]


# ============================================================
# Handler Functions
# ============================================================

def _save_state():
    """Mark state as dirty for persistence."""
    state_manager.mark_dirty()
    state_manager.save()


def handle_calculate_chart():
    """Handle natal chart calculation."""
    # Collect birth data from session state
    birth_data = {
        "name": st.session_state.get("input_name", "Иван"),
        "date": st.session_state.get("input_birth_date", date(1990, 5, 15)).strftime("%Y-%m-%d"),
        "time": st.session_state.get("input_birth_time", time(14, 30)).strftime("%H:%M"),
        "latitude": st.session_state.get("profile_data", {}).get("latitude", 55.7558),
        "longitude": st.session_state.get("profile_data", {}).get("longitude", 37.6173),
        "utc_offset_hours": st.session_state.get("profile_data", {}).get("utc_offset", 3.0),
    }
    
    # Collect settings
    settings = {
        "house_system": st.session_state.get("select_house_system", "placidus"),
        "zodiac": "sidereal" if st.session_state.get("radio_zodiac", "Тропический") == "Сидерический" else "tropical",
        "ayanamsha": {"Лахири": "lahiri", "Раман": "raman", "Кришнамурти": "krishnamurti", "Фаган-Брэдли": "fagan_brady"}.get(
            st.session_state.get("select_ayanamsha", "Лахири"), "lahiri"
        ),
        "include_chiron": st.session_state.get("chk_chiron", True),
        "include_nodes": st.session_state.get("chk_nodes", True),
        "include_part_of_fortune": st.session_state.get("chk_fortune", True),
        "include_angles": st.session_state.get("chk_angles", True),
        "ephe_path": st.session_state.get("input_ephe_path", "ephe"),
    }
    
    display_profile_name = state.display_profile_name
    
    try:
        result = controllers["chart"].calculate_chart(
            birth_data=birth_data,
            settings=settings,
            display_profile_name=display_profile_name,
        )
        
        state.chart_result = result
        state.birth = birth_data
        state.settings = settings
        state.chart_last_calculated = date.today().isoformat()
        
        # Clear transit/progression results
        state.transit_result = None
        state.transit_mode_used = None
        state.transit_period = None
        state.progression_result = None
        
        _save_state()
        st.rerun()
        
    except Exception as error:
        state.last_error = f"Ошибка расчёта карты: {error}"
        st.error(state.last_error)


def handle_load_profile(profile_name: str):
    """Handle loading a birth profile."""
    try:
        profile = controllers["profile"].load_profile(profile_name)
        state.current_profile = profile
        state.editing_profile_name = None
        
        # Update session state for form fields
        st.session_state["input_name"] = profile.name
        st.session_state["input_birth_date"] = profile.birth_date
        st.session_state["input_birth_time"] = profile.birth_time
        st.session_state["coord_source"] = "Вручную"
        st.session_state["input_latitude"] = profile.latitude
        st.session_state["input_longitude"] = profile.longitude
        st.session_state["input_utc_offset"] = profile.utc_offset_hours
        st.session_state["profile_data"] = {
            "name": profile.name,
            "birth_date": profile.birth_date,
            "birth_time": profile.birth_time,
            "coord_source": "Вручную",
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "utc_offset": profile.utc_offset_hours,
        }
        
        _save_state()
        st.rerun()
        
    except Exception as error:
        st.error(f"Ошибка загрузки профиля: {error}")


def handle_save_profile(editing_name: str = None):
    """Handle saving a birth profile."""
    name = st.session_state.get("input_name", "").strip()
    if not name:
        st.warning("Введите имя перед сохранением.")
        return
    
    birth_date = st.session_state.get("input_birth_date", date.today())
    birth_time = st.session_state.get("input_birth_time", time(0, 0))
    latitude = st.session_state.get("profile_data", {}).get("latitude", 0.0)
    longitude = st.session_state.get("profile_data", {}).get("longitude", 0.0)
    utc_offset = st.session_state.get("profile_data", {}).get("utc_offset", 0.0)
    
    profile_data = {
        "name": name,
        "date": birth_date.strftime("%Y-%m-%d"),
        "time": birth_time.strftime("%H:%M"),
        "latitude": latitude,
        "longitude": longitude,
        "utc_offset_hours": utc_offset,
    }
    
    try:
        controllers["profile"].save_profile(profile_data)
        if editing_name and name != editing_name:
            controllers["profile"].delete_profile(editing_name)
            state.editing_profile_name = None
        elif editing_name:
            state.editing_profile_name = None
        _save_state()
        st.rerun()
    except Exception as error:
        st.error(f"Ошибка сохранения профиля: {error}")


def handle_edit_profile(profile_name: str):
    """Handle editing a birth profile."""
    handle_load_profile(profile_name)
    state.editing_profile_name = profile_name
    _save_state()
    st.rerun()


def handle_delete_profile(profile_name: str):
    """Handle deleting a birth profile."""
    try:
        controllers["profile"].delete_profile(profile_name)
        st.session_state["confirm_delete_profile"] = False
        if state.editing_profile_name == profile_name:
            state.editing_profile_name = None
        _save_state()
        st.rerun()
    except Exception as error:
        st.error(f"Ошибка удаления профиля: {error}")


def handle_apply_display_profile(profile_name: str):
    """Handle applying a display profile."""
    try:
        controllers["display_profile"].set_current_profile(profile_name)
        state.display_profile_name = profile_name
        state.flag_recalculate_chart = True
        _save_state()
        st.rerun()
    except Exception as error:
        state.display_profile_error = str(error)
        st.error(f"Ошибка применения профиля отображения: {error}")


def handle_save_display_profile(profile_name: str):
    """Handle saving a display profile."""
    profile_name = profile_name.strip()
    if not profile_name:
        st.warning("Введите имя профиля отображения перед сохранением.")
        return
    
    from ui_streamlit.components.display_profile_editor import collect_editor_state
    profile_data = collect_editor_state(st.session_state)
    profile_data["name"] = profile_name
    
    # Validate
    errors = controllers["display_profile"].validate_profile(
        controllers["display_profile"]._dict_to_profile(profile_data)
    )
    if errors:
        for err in errors:
            st.error(err)
        return
    
    try:
        controllers["display_profile"].save_profile(
            controllers["display_profile"]._dict_to_profile(profile_data)
        )
        state.sel_display_profile_name = profile_name
        state.display_profile_selector = profile_name
        _save_state()
        st.rerun()
    except Exception as error:
        st.error(f"Ошибка сохранения профиля отображения: {error}")


def trigger_recalc():
    """Trigger chart recalculation."""
    state.flag_recalculate_chart = True
    _save_state()


def handle_calculate_transits(transit_mode: str, start_date: date, end_date: date, filter_planets: list, filter_aspects: list):
    """Handle transit calculation."""
    if not state.chart_result:
        st.error("Сначала рассчитайте натальную карту.")
        return
    
    natal_objects = state.chart_result["objects"]
    
    transit_settings = dict(state.settings)
    if "enabled_planets" in transit_settings:
        transit_settings["transit_planets"] = list(transit_settings["enabled_planets"])
    
    mode_map = {
        "Быстрый (по дням)": "calendar",
        "Точный (с временем аспектов)": "precise",
        "Периоды активности": "periods",
    }
    mode = mode_map.get(transit_mode, "calendar")
    
    filter_p = filter_planets if filter_planets else None
    filter_a = filter_aspects if filter_aspects else None
    
    with st.spinner("Расчёт транзитов... Пожалуйста, подождите."):
        try:
            if mode == "periods":
                result = controllers["transit"].calculate_transits(
                    natal_objects,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    controllers["transit"].get_default_settings(),
                    mode=mode,
                    filter_planets=filter_p,
                    filter_aspects=filter_a,
                )
                state.transit_mode_used = "periods"
            elif mode == "precise":
                result = controllers["transit"].calculate_transits(
                    natal_objects,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    controllers["transit"].get_default_settings(),
                    mode=mode,
                    filter_planets=filter_p,
                    filter_aspects=filter_a,
                )
                state.transit_mode_used = "precise"
            else:
                result = controllers["transit"].calculate_transits(
                    natal_objects,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    controllers["transit"].get_default_settings(),
                    mode=mode,
                    filter_planets=filter_p,
                    filter_aspects=filter_a,
                )
                state.transit_mode_used = "calendar"
            
            state.transit_result = result
            state.transit_period = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            _save_state()
            st.rerun()
            
        except Exception as error:
            st.error(f"Ошибка расчёта транзитов: {error}")


def handle_calculate_progressions():
    """Handle progression calculation."""
    if not state.chart_result:
        st.error("Сначала рассчитайте натальную карту.")
        return
    
    birth_data = state.birth
    progression_date = state.progression_date
    progression_type = state.progression_type
    
    try:
        result = controllers["progression"].calculate_progressions(
            birth_data=birth_data,
            progression_date=progression_date,
            progression_type=progression_type,
            display_profile_name=state.display_profile_name,
        )
        
        state.progression_result = result
        _save_state()
        st.rerun()
        
    except Exception as error:
        st.error(f"Ошибка расчёта прогрессий: {error}")


# ============================================================
# Auto-recalculation
# ============================================================
if state.flag_recalculate_chart:
    state.flag_recalculate_chart = False
    handle_calculate_chart()


# ============================================================
# Render Main Page
# ============================================================
st.title("🌟 Astro Processor")
st.markdown("Локальный модульный астрологический процессор")

# Panel toggles
tg1, tg2, tg3 = st.columns([1, 8, 1])
with tg1:
    if st.button("◀ Скрыть" if state.show_left_panel else "▶ Показать", key="btn_toggle_left", use_container_width=True):
        state.show_left_panel = not state.show_left_panel
        _save_state()
with tg3:
    if st.button("Скрыть ▶" if state.show_right_panel else "Показать ◀", key="btn_toggle_right", use_container_width=True):
        state.show_right_panel = not state.show_right_panel
        _save_state()

# Render the chart page
render_chart_page(
    chart_controller=controllers["chart"],
    transit_controller=controllers["transit"],
    progression_controller=controllers["progression"],
    display_profile_controller=controllers["display_profile"],
    city_controller=controllers["city"],
    profile_controller=controllers["profile"],
    state=state,
)


# ============================================================
# Save state on exit (Streamlit handles this via session_state)
# ============================================================
# State is automatically persisted via session_state