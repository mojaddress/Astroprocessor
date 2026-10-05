"""
Display Profile Editor Component - UI for customizing display profiles.
"""
import streamlit as st
from typing import Callable, Optional, List

from astro_core.controllers import DisplayProfileController
from astro_core.constants import get_planet_name_ru, get_aspect_name_ru
from astro_core.display_profiles import ALL_PLANETS, ALL_ASPECTS, DEFAULT_ORBS
from astro_core.chart_svg import PLANET_COLORS, ASPECT_COLORS


def render_display_profile_panel(
    display_profile_controller: DisplayProfileController,
    state,
    on_apply_profile: Callable,
    on_save_profile: Callable,
):
    """Render the display profile selection and editor panel."""
    
    st.markdown("##### 🎨 Профиль отображения")
    
    display_profiles = display_profile_controller.list_profiles()
    display_profile_options = [p.name for p in display_profiles]
    if not display_profile_options:
        display_profile_options = ["full"]
    
    selected_display_profile = st.selectbox(
        "Профиль", options=display_profile_options, key="display_profile_selector",
    )
    
    new_display_profile_name = st.text_input(
        "Имя для сохранения",
        value=state.sel_display_profile_name if hasattr(state, 'sel_display_profile_name') else "full",
        key="new_display_profile_name",
    )
    
    dp_c1, dp_c2 = st.columns(2)
    with dp_c1:
        if st.button("📥 Применить", key="btn_apply_display_profile", use_container_width=True):
            on_apply_profile(selected_display_profile)
    with dp_c2:
        if st.button("💾 Сохранить", key="btn_save_display_profile", use_container_width=True):
            on_save_profile(new_display_profile_name)
    
    if state.get("display_profile_error"):
        st.error(f"Ошибка применения профиля отображения: {state['display_profile_error']}")
        state["display_profile_error"] = None
    
    # Editor
    with st.expander("Настроить объекты, аспекты и внешний вид"):
        # Initialize session state for editor if not present
        _init_editor_state(state)
        
        # Planets
        display_planets = st.multiselect(
            "Планеты", options=list(ALL_PLANETS),
            format_func=get_planet_name_ru, key="sel_planets",
        )
        st.caption("Хирон, узлы, Part of Fortune и ASC/MC — чекбоксы в «Дополнительных настройках».")
        
        # Aspects
        display_aspects = st.multiselect(
            "Аспекты", options=list(ALL_ASPECTS),
            format_func=get_aspect_name_ru, key="sel_aspects",
        )
        
        # Orbs
        st.markdown("**Орбы аспекций (°)**")
        orb_c1, orb_c2 = st.columns(2)
        for idx, aspect_name in enumerate(ALL_ASPECTS):
            col = orb_c1 if idx % 2 == 0 else orb_c2
            with col:
                st.number_input(
                    get_aspect_name_ru(aspect_name),
                    min_value=0.0, max_value=30.0, step=0.5,
                    key=f"orb_{aspect_name}",
                )
        
        st.divider()
        st.markdown("**Внешний вид**")
        
        # Label mode
        label_mode_display = st.radio(
            "Подписи",
            ["symbols", "words", "both"],
            format_func=lambda m: {"symbols": "Символы", "words": "Слова", "both": "Символы + слова"}[m],
            horizontal=True, key="radio_label_mode",
        )
        
        ap_c1, ap_c2 = st.columns(2)
        with ap_c1:
            show_aspects_ui = st.checkbox("Показать аспекты", key="chk_show_aspects")
            show_houses_ui = st.checkbox("Показать дома", key="chk_show_houses")
        with ap_c2:
            chart_size_ui = st.slider("Размер карты", min_value=600, max_value=1600, step=100, key="slider_chart_size")
            dot_size_ui = st.slider("Размер точек планет", min_value=3, max_value=10, key="slider_dot_size")
        
        # Planet colors
        st.markdown("**Цвета планет**")
        for row_start in range(0, len(ALL_PLANETS), 2):
            pc1, pc2 = st.columns(2)
            planet_a = ALL_PLANETS[row_start]
            with pc1:
                st.color_picker(get_planet_name_ru(planet_a), key=f"color_{planet_a}")
            if row_start + 1 < len(ALL_PLANETS):
                planet_b = ALL_PLANETS[row_start + 1]
                with pc2:
                    st.color_picker(get_planet_name_ru(planet_b), key=f"color_{planet_b}")
        
        # Aspect colors
        st.markdown("**Цвета аспектов**")
        for row_start in range(0, len(ALL_ASPECTS), 2):
            ac1, ac2 = st.columns(2)
            aspect_a = ALL_ASPECTS[row_start]
            with ac1:
                st.color_picker(get_aspect_name_ru(aspect_a), key=f"acolor_{aspect_a}")
            if row_start + 1 < len(ALL_ASPECTS):
                aspect_b = ALL_ASPECTS[row_start + 1]
                with ac2:
                    st.color_picker(get_aspect_name_ru(aspect_b), key=f"acolor_{aspect_b}")


def _init_editor_state(state):
    """Initialize editor session state with defaults from current profile."""
    from astro_core.controllers.display_profile_controller import ALL_PLANETS, ALL_ASPECTS, DEFAULT_ORBS
    from astro_core.chart_svg import PLANET_COLORS, ASPECT_COLORS
    
    if "sel_planets" not in state:
        state["sel_planets"] = list(ALL_PLANETS)
    if "sel_aspects" not in state:
        state["sel_aspects"] = list(ALL_ASPECTS)
    if "chk_chiron" not in state:
        state["chk_chiron"] = True
    if "chk_nodes" not in state:
        state["chk_nodes"] = True
    if "chk_fortune" not in state:
        state["chk_fortune"] = True
    if "chk_angles" not in state:
        state["chk_angles"] = True
    for aspect in ALL_ASPECTS:
        if f"orb_{aspect}" not in state:
            state[f"orb_{aspect}"] = float(DEFAULT_ORBS[aspect])
        if f"acolor_{aspect}" not in state:
            state[f"acolor_{aspect}"] = ASPECT_COLORS.get(aspect, "#888888")
    for planet in ALL_PLANETS:
        if f"color_{planet}" not in state:
            state[f"color_{planet}"] = PLANET_COLORS.get(planet, "#000000")
    if "radio_label_mode" not in state:
        state["radio_label_mode"] = "symbols"
    if "chk_show_aspects" not in state:
        state["chk_show_aspects"] = True
    if "chk_show_houses" not in state:
        state["chk_show_houses"] = True
    if "slider_chart_size" not in state:
        state["slider_chart_size"] = 800
    if "slider_dot_size" not in state:
        state["slider_dot_size"] = 5


def collect_editor_state(state) -> dict:
    """Collect all editor state into a profile dict."""
    from astro_core.controllers.display_profile_controller import ALL_PLANETS, ALL_ASPECTS, DEFAULT_ORBS
    from astro_core.constants import PLANET_COLORS, ASPECT_COLORS
    
    profile = {
        "name": state.get("new_display_profile_name", "").strip(),
        "description": "Пользовательский профиль отображения",
        "objects": {},
        "aspects": {},
        "appearance": {},
    }
    
    # Objects
    cur_planets = state.get("sel_planets", [])
    for planet in ALL_PLANETS:
        profile["objects"][planet] = planet in cur_planets
    profile["objects"]["Chiron"] = bool(state.get("chk_chiron", True))
    profile["objects"]["LunarNodes"] = bool(state.get("chk_nodes", True))
    profile["objects"]["PartOfFortune"] = bool(state.get("chk_fortune", True))
    profile["objects"]["Angles"] = bool(state.get("chk_angles", True))
    
    # Aspects
    cur_aspects = state.get("sel_aspects", [])
    for aspect in ALL_ASPECTS:
        profile["aspects"][aspect] = {
            "enabled": aspect in cur_aspects,
            "orb": float(state.get(f"orb_{aspect}", DEFAULT_ORBS[aspect])),
        }
    
    # Appearance
    profile["appearance"] = {
        "label_mode": state.get("radio_label_mode", "symbols"),
        "show_houses": bool(state.get("chk_show_houses", True)),
        "show_aspect_lines": bool(state.get("chk_show_aspects", True)),
        "chart_size": int(state.get("slider_chart_size", 800)),
        "planet_dot_size": int(state.get("slider_dot_size", 5)),
        "planet_colors": {
            p: state.get(f"color_{p}", PLANET_COLORS.get(p, "#000000"))
            for p in ALL_PLANETS
        },
        "aspect_colors": {
            a: state.get(f"acolor_{a}", ASPECT_COLORS.get(a, "#888888"))
            for a in ALL_ASPECTS
        },
    }
    
    return profile


def apply_profile_to_editor(state, profile_name: str, display_profile_controller: DisplayProfileController):
    """Apply a display profile to the editor state."""
    try:
        profile = display_profile_controller.load_profile(profile_name)
        data = display_profile_controller._profile_to_dict(profile)
        
        objects = data.get("objects", {})
        state["chk_chiron"] = bool(objects.get("Chiron", True))
        state["chk_nodes"] = bool(objects.get("LunarNodes", True))
        state["chk_fortune"] = bool(objects.get("PartOfFortune", True))
        state["chk_angles"] = bool(objects.get("Angles", True))
        state["sel_planets"] = [p for p in ALL_PLANETS if objects.get(p, True)]
        
        aspects = data.get("aspects", {})
        state["sel_aspects"] = [a for a in ALL_ASPECTS if aspects.get(a, {}).get("enabled", True)]
        for aspect in ALL_ASPECTS:
            state[f"orb_{aspect}"] = float(aspects.get(aspect, {}).get("orb", DEFAULT_ORBS[aspect]))
        
        appearance = data.get("appearance", {})
        state["radio_label_mode"] = appearance.get("label_mode", "symbols")
        state["chk_show_aspects"] = bool(appearance.get("show_aspect_lines", True))
        state["chk_show_houses"] = bool(appearance.get("show_houses", True))
        state["slider_chart_size"] = int(appearance.get("chart_size", 800))
        state["slider_dot_size"] = int(appearance.get("planet_dot_size", 5))
        for planet in ALL_PLANETS:
            if planet in appearance.get("planet_colors", {}):
                state[f"color_{planet}"] = appearance["planet_colors"][planet]
        for aspect in ALL_ASPECTS:
            if aspect in appearance.get("aspect_colors", {}):
                state[f"acolor_{aspect}"] = appearance["aspect_colors"][aspect]
        
        state["sel_display_profile_name"] = profile_name
        state["display_profile_selector"] = profile_name
        state["flag_recalculate_chart"] = True
        
    except Exception as error:
        state["display_profile_error"] = str(error)