"""
Transit Panel Component - UI for transit calculations.
"""
import streamlit as st
from datetime import date, time, timedelta
from typing import Callable, Optional, List

from astro_core.controllers import TransitController, CityController
from astro_core.constants import (
    get_planet_name_ru, get_aspect_name_ru,
    DEFAULT_TRANSIT_PLANETS, ASPECT_DEFINITIONS
)


def render_transit_panel(
    transit_controller: TransitController,
    city_controller: CityController,
    state,
    on_calculate_transits: Callable,
):
    """Render the right panel with transit controls."""
    
    st.markdown("##### 🔄 Управление транзитами")
    
    if not state.chart_result:
        st.info("Сначала рассчитайте натальную карту в левой панели — транзиты строятся относительно неё.")
        return
    
    # Mode selection
    transit_mode = st.radio(
        "Режим",
        ["Быстрый (по дням)", "Точный (с временем аспектов)", "Периоды активности"],
        index=0,
        key="transit_mode_radio",
    )
    
    # Get enabled planets from chart settings
    planet_options = list(
        state.settings.get("enabled_planets", DEFAULT_TRANSIT_PLANETS)
    )
    selected_planets = st.multiselect(
        "Транзитные планеты (пусто = все)", options=planet_options,
        format_func=get_planet_name_ru, default=[],
        key="transit_filter_planets",
    )
    
    aspect_options = [a["name"] for a in ASPECT_DEFINITIONS]
    selected_aspects = st.multiselect(
        "Аспекты (пусто = все)", options=aspect_options,
        format_func=get_aspect_name_ru, default=[],
        key="transit_filter_aspects",
    )
    
    st.divider()
    st.markdown("##### 📅 Дата транзита")
    
    # Date navigation
    def _shift_transit_date(days):
        state.current_transit_date += timedelta(days=days)
        st.rerun()
    
    nav1, nav2 = st.columns(2)
    with nav1:
        st.button("⏪ -1 мес", on_click=_shift_transit_date, args=(-30,), use_container_width=True, key="btn_transit_minus_month")
        st.button("◀️ -1 день", on_click=_shift_transit_date, args=(-1,), use_container_width=True, key="btn_transit_minus_day")
    with nav2:
        st.button("+1 день ▶️", on_click=_shift_transit_date, args=(1,), use_container_width=True, key="btn_transit_plus_day")
        st.button("+1 мес ⏩", on_click=_shift_transit_date, args=(30,), use_container_width=True, key="btn_transit_plus_month")
    
    st.date_input("Дата транзита", key="current_transit_date")
    
    st.divider()
    st.markdown("##### 🏙️ Город транзита")
    
    transit_location_mode = st.radio(
        "Привязка к городу", ["Без города", "Выбрать город"],
        index=0, key="transit_location_mode",
    )
    
    if transit_location_mode == "Выбрать город":
        transit_city_query = st.text_input("Поиск города транзита", value="", key="transit_city_query")
        if transit_city_query.strip():
            found_transit_cities = city_controller.search_cities(transit_city_query, limit=10)
        else:
            found_transit_cities = city_controller.get_all_cities()[:10]
        
        if found_transit_cities:
            transit_city_options = [city_controller.get_city_display_name(c) for c in found_transit_cities]
            selected_transit_city_display = st.selectbox(
                "Город транзита", options=transit_city_options, index=0, key="selected_transit_city",
            )
            
            chosen_tc = None
            for c in found_transit_cities:
                if city_controller.get_city_display_name(c) == selected_transit_city_display:
                    chosen_tc = c
                    break
            
            if chosen_tc:
                state.transit_city = chosen_tc
                st.caption(f"📍 {chosen_tc.name}, {chosen_tc.country}")
            else:
                st.warning("Город не найден.")
                state.transit_city = None
        else:
            state.transit_city = None
    else:
        state.transit_city = None
    
    st.divider()
    
    # Date range selection
    transit_date_option = st.radio("Тип периода", ["Одна дата", "Диапазон дат"], index=1, key="transit_date_option")
    
    if transit_date_option == "Одна дата":
        transit_single_date = st.date_input(
            "Дата транзитов", value=date.today(),
            min_value=date(1900, 1, 1), max_value=date(2100, 12, 31),
            key="transit_single_date",
        )
        state.transit_start_date = transit_single_date
        state.transit_end_date = transit_single_date
    else:
        transit_start_date = st.date_input(
            "Дата начала", value=state.transit_start_date,
            min_value=date(1900, 1, 1), max_value=date(2100, 12, 31),
            key="transit_start_date",
        )
        transit_end_date = st.date_input(
            "Дата конца", value=state.transit_end_date,
            min_value=date(1900, 1, 1), max_value=date(2100, 12, 31),
            key="transit_end_date",
        )
        state.transit_start_date = transit_start_date
        state.transit_end_date = transit_end_date
    
    st.divider()
    
    # Calculate button
    if st.button("🔮 Рассчитать транзиты", type="primary", use_container_width=True, key="btn_calculate_transits"):
        on_calculate_transits(
            transit_mode=transit_mode,
            start_date=state.transit_start_date,
            end_date=state.transit_end_date,
            filter_planets=selected_planets,
            filter_aspects=selected_aspects,
        )


def render_transit_results(state):
    """Render transit calculation results."""
    if not state.transit_result:
        return
    
    st.markdown("### Результаты транзитов")
    
    mode = state.transit_mode_used or "calendar"
    
    if mode == "periods":
        st.markdown("**Периоды активности транзитов**")
        if state.transit_result:
            import pandas as pd
            df = pd.DataFrame(state.transit_result)
            if not df.empty:
                # Format columns
                display_cols = ["transit_planet", "aspect", "natal_point", "start_date", "exact_date", "end_date", "orb", "strength"]
                available_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[available_cols], use_container_width=True)
            else:
                st.info("Нет периодов активности для выбранных фильтров.")
    
    elif mode == "precise":
        st.markdown("**Точные события транзитов**")
        if state.transit_result:
            import pandas as pd
            df = pd.DataFrame(state.transit_result)
            if not df.empty:
                display_cols = ["exact_datetime", "direction", "transit_planet", "aspect", "natal_point", "orb"]
                available_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[available_cols], use_container_width=True)
            else:
                st.info("Нет точных событий для выбранных фильтров.")
    
    else:
        st.markdown("**Календарь транзитов**")
        if state.transit_result:
            import pandas as pd
            df = pd.DataFrame(state.transit_result)
            if not df.empty:
                display_cols = ["date", "transit_planet", "aspect", "natal_point", "orb", "strength"]
                available_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[available_cols], use_container_width=True)
            else:
                st.info("Нет транзитов для выбранного периода.")
    
    # Download button
    if state.transit_result:
        import json
        st.download_button(
            "📥 Скачать транзиты (JSON)",
            data=json.dumps(state.transit_result, ensure_ascii=False, indent=2),
            file_name="transits.json",
            mime="application/json",
        )