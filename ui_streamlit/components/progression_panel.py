"""
Progression Panel Component - UI for progression calculations.
"""
import streamlit as st
from datetime import date
from typing import Callable, Optional

from astro_core.controllers import ProgressionController


def render_progression_panel(
    progression_controller: ProgressionController,
    state,
    on_calculate_progressions: Callable,
):
    """Render the progression panel in the sidebar or tab."""
    
    st.markdown("##### 🔄 Прогрессии")
    
    if not state.chart_result:
        st.info("Сначала рассчитайте натальную карту.")
        return
    
    # Progression date
    progression_date = st.date_input(
        "Дата прогрессии", value=state.progression_date,
        min_value=date(1900, 1, 1), max_value=date(2100, 12, 31),
        key="progression_date",
    )
    state.progression_date = progression_date
    
    # Progression type
    progression_type = st.radio(
        "Тип прогрессий",
        ["Вторичные (день за год)", "Солнечная дуга"],
        index=0 if state.progression_type == "secondary" else 1,
        key="progression_type_radio",
    )
    state.progression_type = "secondary" if progression_type == "Вторичные (день за год)" else "solar_arc"
    
    # Calculate button
    if st.button("🔮 Рассчитать прогрессии", type="primary", use_container_width=True, key="btn_calculate_progressions"):
        on_calculate_progressions()


def render_progression_results(state):
    """Render progression calculation results in a tab."""
    if not state.progression_result:
        return
    
    result = state.progression_result
    
    st.markdown(f"### Прогрессии: {result.progression_type}")
    st.caption(f"Дата: {result.progression_date} | Возраст: {result.age_years:.2f} лет")
    
    # Progressed planets
    if result.progressed_planets:
        st.markdown("**Прогрессивные планеты**")
        import pandas as pd
        df_planets = pd.DataFrame(result.progressed_planets)
        display_cols = ["name", "longitude", "sign", "degree", "speed", "retrograde"]
        available_cols = [c for c in display_cols if c in df_planets.columns]
        st.dataframe(df_planets[available_cols], use_container_width=True)
    
    # Progressed points (ASC, MC, Part of Fortune)
    if result.progressed_points:
        st.markdown("**Прогрессивные точки**")
        df_points = pd.DataFrame(result.progressed_points)
        display_cols = ["name", "longitude", "sign", "degree"]
        available_cols = [c for c in display_cols if c in df_points.columns]
        st.dataframe(df_points[available_cols], use_container_width=True)
    
    # Aspects
    if result.aspects:
        st.markdown("**Аспекты прогрессий к натальным точкам**")
        df_aspects = pd.DataFrame(result.aspects)
        display_cols = ["progressed_planet", "aspect", "natal_point", "orb", "strength", "applying"]
        available_cols = [c for c in display_cols if c in df_aspects.columns]
        st.dataframe(df_aspects[available_cols], use_container_width=True)
    else:
        st.info("Аспекты не найдены.")
    
    # Download button
    import json
    from dataclasses import asdict
    download_data = {
        "progression_type": result.progression_type,
        "progression_date": result.progression_date,
        "age_years": result.age_years,
        "progressed_planets": result.progressed_planets,
        "progressed_points": result.progressed_points,
        "aspects": result.aspects,
    }
    st.download_button(
        "📥 Скачать прогрессии (JSON)",
        data=json.dumps(download_data, ensure_ascii=False, indent=2),
        file_name="progressions.json",
        mime="application/json",
    )