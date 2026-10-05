"""
Chart Page - main chart display page.
"""
import streamlit as st
from datetime import date

from astro_core.controllers import ChartController, TransitController, ProgressionController
from astro_core.controllers import DisplayProfileController, CityController, ProfileController
from ui_streamlit.components.birth_input import render_birth_input_panel, render_additional_settings_panel
from ui_streamlit.components.display_profile_editor import (
    render_display_profile_panel,
    collect_editor_state,
    apply_profile_to_editor,
)
from ui_streamlit.components.transit_panel import render_transit_panel, render_transit_results
from ui_streamlit.components.progression_panel import render_progression_panel, render_progression_results
from ui_streamlit.components.chart_display import (
    render_chart_tab, render_objects_tab, render_houses_tab, render_aspects_tab, render_json_tab
)


def render_chart_page(
    chart_controller: ChartController,
    transit_controller: TransitController,
    progression_controller: ProgressionController,
    display_profile_controller: DisplayProfileController,
    city_controller: CityController,
    profile_controller: ProfileController,
    state,
):
    """Render the main chart page with all tabs."""
    
    # Left panel - birth input and display profile
    with st.sidebar:
        # Birth input panel
        birth_data = render_birth_input_panel(
            chart_controller, city_controller, profile_controller, state,
            on_calculate=_handle_calculate_chart,
            on_profile_load=_handle_load_profile,
            on_profile_save=_handle_save_profile,
            on_profile_edit=_handle_edit_profile,
            on_profile_delete=_handle_delete_profile,
        )
        
        # Additional settings
        additional_settings = render_additional_settings_panel(state, _trigger_recalc)
        
        # Display profile panel
        render_display_profile_panel(
            display_profile_controller, state,
            on_apply_profile=_handle_apply_display_profile,
            on_save_profile=_handle_save_display_profile,
        )
    
    # Main content - tabs
    tab_chart, tab_objects, tab_houses, tab_aspects, tab_progressions, tab_json = st.tabs(
        ["🌌 Карта", "Объекты", "Дома", "Аспекты", "🔄 Прогрессии", "JSON"]
    )
    
    with tab_chart:
        render_chart_tab(chart_controller, display_profile_controller, state, transit_controller)
    
    with tab_objects:
        render_objects_tab(state)
    
    with tab_houses:
        render_houses_tab(state)
    
    with tab_aspects:
        render_aspects_tab(state)
    
    with tab_progressions:
        # Progression panel in sidebar or here
        with st.sidebar:
            render_progression_panel(progression_controller, state, _handle_calculate_progressions)
        render_progression_results(state)
    
    with tab_json:
        render_json_tab(state)
    
    # Transit panel in right sidebar area (or we can put it in sidebar too)
    # For now, let's put transit controls in an expander in the sidebar
    with st.sidebar:
        st.divider()
        render_transit_panel(transit_controller, city_controller, state, _handle_calculate_transits)
        if state.transit_result:
            st.divider()
            render_transit_results(state)


# Handler functions - these will be defined in app_streamlit.py
def _handle_calculate_chart(birth_data, additional_settings, display_profile_name):
    pass

def _handle_load_profile(profile_name):
    pass

def _handle_save_profile(editing_name):
    pass

def _handle_edit_profile(profile_name):
    pass

def _handle_delete_profile(profile_name):
    pass

def _handle_apply_display_profile(profile_name):
    pass

def _handle_save_display_profile(profile_name):
    pass

def _trigger_recalc():
    pass

def _handle_calculate_transits(transit_mode, start_date, end_date, filter_planets, filter_aspects):
    pass

def _handle_calculate_progressions():
    pass