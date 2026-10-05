"""
Chart Display Component - UI for rendering charts.
"""
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional

from astro_core.chart_svg import (
    render_natal_chart_svg,
    render_transit_chart_svg,
    PLANET_COLORS,
    ASPECT_COLORS,
)
from astro_core.chart_interactive import render_interactive_chart, render_interactive_transit_chart
from astro_core.display_profiles import get_render_kwargs, ALL_PLANETS, ALL_ASPECTS
from astro_core.controllers import ChartController, DisplayProfileController


def render_chart_tab(
    chart_controller: ChartController,
    display_profile_controller: DisplayProfileController,
    state,
    transit_controller=None,
):
    """Render the chart tab with interactive SVG."""
    
    if not state.chart_result:
        st.info("Введите данные рождения в левой панели и нажмите «Рассчитать карту».")
        return
    
    result = state.chart_result
    
    # Chart header
    chart_name = result["birth"].get("name", "Chart")
    st.subheader(f"Натальная карта: {chart_name}")
    
    if result.get("warnings"):
        with st.expander("Предупреждения", expanded=False):
            for warning in result["warnings"]:
                st.warning(warning)
    
    # Chart type selector
    _saved_chart_type_options = ["Натальная карта", "Транзитная карта"]
    _saved_chart_type = state.get("chart_type", "Натальная карта")
    _saved_chart_type_index = _saved_chart_type_options.index(_saved_chart_type) if _saved_chart_type in _saved_chart_type_options else 0
    
    chart_type = st.radio(
        "Тип карты",
        _saved_chart_type_options,
        index=_saved_chart_type_index,
        key="chart_type",
    )
    
    # Get appearance settings from display profile
    profile = display_profile_controller.get_current_profile()
    if profile:
        appearance = display_profile_controller.get_appearance_settings()
    else:
        appearance = {}
    
    chart_size = state.get("slider_chart_size", 800)
    label_mode = state.get("radio_label_mode", "symbols")
    show_aspects = state.get("chk_show_aspects", True)
    show_houses = state.get("chk_show_houses", True)
    dot_size = state.get("slider_dot_size", 5)
    planet_colors = {
        p: state.get(f"color_{p}", PLANET_COLORS.get(p, "#000000"))
        for p in ALL_PLANETS
    }
    aspect_colors = {
        a: state.get(f"acolor_{a}", ASPECT_COLORS.get(a, "#888888"))
        for a in ALL_ASPECTS
    }
    
    if chart_type == "Натальная карта":
        # Interactive chart
        interactive_html = render_interactive_chart(
            result, size=chart_size, show_aspects=show_aspects, label_mode=label_mode,
            show_houses=show_houses, planet_dot_size=dot_size,
            planet_colors=planet_colors, aspect_colors=aspect_colors,
        )
        components.html(interactive_html, height=chart_size + 60, scrolling=True)
        st.caption("💡 Колесо мыши — зум, зажать и двигать — перетаскивание. Внешний вид настраивается в «🎨 Профиле отображения» слева.")
        
        # Static SVG for download
        static_svg = render_natal_chart_svg(
            result, size=chart_size, show_aspects=show_aspects, label_mode=label_mode,
            show_houses=show_houses, planet_dot_size=dot_size,
            planet_colors=planet_colors, aspect_colors=aspect_colors,
        )
        st.download_button("📥 Скачать карту (SVG)", data=static_svg, file_name="natal_chart.svg", mime="image/svg+xml")
    
    else:
        # Transit chart
        transit_date_for_chart = state.get("current_transit_date", date.today())
        transit_city = state.get("transit_city")
        
        transit_houses = None
        transit_additional_points = None
        
        if transit_city is not None:
            try:
                from astro_core.timezone_service import get_utc_offset_hours
                from datetime import datetime as dt_datetime, time
                
                transit_tz_name = transit_city.get("timezone", "")
                if transit_tz_name:
                    transit_dt_for_tz = dt_datetime.combine(transit_date_for_chart, time(12, 0))
                    transit_utc_offset_hours = get_utc_offset_hours(transit_tz_name, transit_dt_for_tz)
                else:
                    transit_utc_offset_hours = 0.0
                
                natal_settings_for_ephe = state.settings
                transit_ephe_path = natal_settings_for_ephe.get("ephe_path", "ephe")
                
                transit_chart_birth = {
                    "name": "Транзит",
                    "date": transit_date_for_chart.strftime("%Y-%m-%d"),
                    "time": "12:00",
                    "latitude": transit_city["latitude"],
                    "longitude": transit_city["longitude"],
                    "utc_offset_hours": transit_utc_offset_hours,
                }
                
                transit_chart_settings = {
                    "include_chiron": False, "include_nodes": False,
                    "include_part_of_fortune": False, "include_angles": True,
                    "ephe_path": transit_ephe_path,
                }
                
                from astro_core.chart import build_natal_chart
                transit_chart_result = build_natal_chart(transit_chart_birth, transit_chart_settings)
                transit_houses = transit_chart_result.get("houses", [])
                transit_additional_points = transit_chart_result.get("additional_points", [])
            except Exception as e:
                st.warning(f"Не удалось рассчитать дома транзита для города: {e}")
        
        try:
            from astro_core.time_service import datetime_to_jd
            from datetime import datetime as dt_datetime, time, timedelta
            
            natal_utc_offset = state.get("birth", {}).get("utc_offset_hours", 0.0)
            transit_dt = dt_datetime.combine(transit_date_for_chart, time(12, 0))
            transit_utc_dt = transit_dt - timedelta(hours=natal_utc_offset)
            transit_jd = datetime_to_jd(transit_utc_dt)
            
            transit_settings = {"include_chiron": False, "include_nodes": False}
            from astro_core.transits import calculate_transit_positions
            transit_planets_list, _ = calculate_transit_positions(transit_jd, transit_settings)
            
            selected_planets = state.get("transit_filter_planets", [])
            if selected_planets:
                transit_planets_list = [p for p in transit_planets_list if p["name"] in selected_planets]
            
            transit_chart_settings = dict(result.get("settings", {}))
            selected_aspects = state.get("transit_filter_aspects", [])
            if selected_aspects:
                transit_chart_settings["enabled_aspects"] = list(selected_aspects)
            
            natal_objects = result.get("objects", [])
            from astro_core.transits import find_transits_on_date
            transit_aspects_list = find_transits_on_date(natal_objects, transit_planets_list, transit_chart_settings)
            
            transit_svg = render_transit_chart_svg(
                result, transit_planets_list, transit_aspects_list,
                size=chart_size, label_mode=label_mode, show_aspects=show_aspects,
                transit_houses=transit_houses, transit_additional_points=transit_additional_points,
                planet_colors=planet_colors, aspect_colors=aspect_colors,
            )
            
            # Interactive transit chart
            interactive_transit_html = render_interactive_transit_chart(
                result, transit_planets_list, transit_aspects_list,
                size=chart_size, show_aspects=show_aspects, label_mode=label_mode,
                transit_houses=transit_houses, transit_additional_points=transit_additional_points,
                planet_colors=planet_colors, aspect_colors=aspect_colors,
            )
            components.html(interactive_transit_html, height=chart_size + 60, scrolling=True)
            
            st.download_button("📥 Скачать транзитную карту (SVG)", data=transit_svg, file_name="transit_chart.svg", mime="image/svg+xml")
            
        except Exception as e:
            st.error(f"Ошибка отрисовки транзитной карты: {e}")


def render_objects_tab(state):
    """Render the objects table tab."""
    if not state.chart_result:
        return
    
    result = state.chart_result
    objects = result.get("objects", [])
    
    if objects:
        import pandas as pd
        df = pd.DataFrame(objects)
        display_cols = ["name", "longitude", "sign", "degree", "house", "retrograde", "speed"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.info("Нет объектов для отображения.")


def render_houses_tab(state):
    """Render the houses table tab."""
    if not state.chart_result:
        return
    
    result = state.chart_result
    houses = result.get("houses", [])
    
    if houses:
        import pandas as pd
        df = pd.DataFrame(houses)
        display_cols = ["number", "longitude", "sign", "degree"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.info("Дома не рассчитаны.")


def render_aspects_tab(state):
    """Render the aspects table tab."""
    if not state.chart_result:
        return
    
    result = state.chart_result
    aspects = result.get("aspects", [])
    
    if aspects:
        import pandas as pd
        df = pd.DataFrame(aspects)
        display_cols = ["planet1", "planet2", "aspect", "orb", "strength", "applying"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.info("Аспекты не найдены.")


def render_json_tab(state):
    """Render the JSON export tab."""
    if not state.chart_result:
        return
    
    import json
    st.code(json.dumps(state.chart_result, ensure_ascii=False, indent=2), language="json")
    st.download_button(
        "📥 Скачать JSON",
        data=json.dumps(state.chart_result, ensure_ascii=False, indent=2),
        file_name="chart.json",
        mime="application/json",
    )