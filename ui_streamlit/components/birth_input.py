"""
Birth Input Component - UI for entering birth data.
"""
import streamlit as st
from datetime import date, time
from typing import Optional, Callable

from astro_core.controllers import ChartController, CityController, ProfileController
from astro_core.controllers.chart_controller import BirthData
from astro_core.controllers.city_controller import City
from astro_core.constants import (
    get_planet_name_ru, get_sign_name_ru, get_aspect_name_ru,
    get_object_type_name_ru, get_direction_name_ru
)


def render_birth_input_panel(
    chart_controller: ChartController,
    city_controller: CityController,
    profile_controller: ProfileController,
    state,
    on_calculate: Callable,
    on_profile_load: Callable,
    on_profile_save: Callable,
    on_profile_edit: Callable,
    on_profile_delete: Callable,
):
    """Render the left panel with birth data input and profiles."""
    
    # --- Profiles Section ---
    st.markdown("##### 👤 Профили")
    
    profiles = profile_controller.list_profiles()
    profile_names = [p.name for p in profiles]
    
    if profile_names:
        selected_profile_name = st.selectbox(
            "Выбрать профиль", options=profile_names, index=None,
            placeholder="— выберите профиль —",
            key="profile_select"
        )
    else:
        st.info("Профилей пока нет.")
        selected_profile_name = None
    
    editing_profile = state.editing_profile_name
    if editing_profile:
        st.info(f"✏️ Редактируется: {editing_profile}")
    
    c_load, c_edit = st.columns(2)
    with c_load:
        if st.button("📂 Загрузить", disabled=(selected_profile_name is None), use_container_width=True, key="btn_load_profile"):
            on_profile_load(selected_profile_name)
    with c_edit:
        if st.button("✏️ Редакт.", disabled=(selected_profile_name is None), use_container_width=True, key="btn_edit_profile"):
            on_profile_edit(selected_profile_name)
    
    confirm_delete = st.checkbox("Подтвердить удаление", value=False, key="confirm_delete_profile")
    if st.button("🗑️ Удалить", disabled=(selected_profile_name is None or not confirm_delete), use_container_width=True, key="btn_delete_profile"):
        on_profile_delete(selected_profile_name)
    
    st.divider()
    
    # --- Birth Data Section ---
    st.markdown("##### 📅 Данные рождения")
    
    # Initialize session state for birth data if not present
    if "input_name" not in st.session_state:
        st.session_state["input_name"] = "Иван"
    if "input_birth_date" not in st.session_state:
        st.session_state["input_birth_date"] = date(1990, 5, 15)
    if "input_birth_time" not in st.session_state:
        st.session_state["input_birth_time"] = time(14, 30)
    
    name = st.text_input("Имя", key="input_name")
    
    _c_date, _c_time = st.columns(2)
    with _c_date:
        birth_date = st.date_input(
            "Дата", value=st.session_state["input_birth_date"],
            min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key="input_birth_date",
        )
    with _c_time:
        birth_time = st.time_input("Время", value=st.session_state["input_birth_time"], key="input_birth_time")
    
    # Show technical chart data if available
    if state.chart_result:
        with st.expander("🔢 Технические данные карты", expanded=False):
            res = state.chart_result
            st.write(f"**Дата:** {res['birth']['date']}")
            st.write(f"**Время:** {res['birth']['time']}")
            st.write(f"**UTC:** {res['utc_datetime']}")
            st.write(f"**Julian Day:** {res['julian_day']}")
    
    # --- City Selection ---
    st.markdown("##### 🏙️ Город рождения")
    
    coord_source = st.radio(
        "Источник координат", ["Из города", "Вручную"],
        index=0, key="coord_source", horizontal=True,
    )
    
    latitude, longitude, utc_offset = 0.0, 0.0, 0.0
    
    if coord_source == "Из города":
        city_query = st.text_input("Поиск города", value="", key="city_query")
        if city_query.strip():
            found_cities = city_controller.search_cities(city_query, limit=10)
        else:
            found_cities = city_controller.get_all_cities()[:10]
        
        if found_cities:
            city_options = [city_controller.get_city_display_name(c) for c in found_cities]
            selected_city_display = st.selectbox("Город", options=city_options, index=0, key="selected_city")
            
            selected_city = None
            for c in found_cities:
                if city_controller.get_city_display_name(c) == selected_city_display:
                    selected_city = c
                    break
            
            if selected_city:
                latitude = selected_city.latitude
                longitude = selected_city.longitude
                timezone_name = selected_city.timezone
                
                if timezone_name:
                    try:
                        from datetime import datetime as dt_datetime
                        birth_dt_for_tz = dt_datetime.combine(birth_date, birth_time)
                        tz_info = city_controller.get_timezone_info(selected_city, birth_dt_for_tz)
                        utc_offset = tz_info["utc_offset"]
                    except ValueError:
                        utc_offset = 0.0
                
                st.caption(f"🏙️ {selected_city_display} · {latitude:.2f}, {longitude:.2f} · UTC{utc_offset:+.1f}")
            else:
                latitude, longitude, utc_offset = 0.0, 0.0, 0.0
        else:
            st.warning("Город не найден.")
    else:
        _c_lat, _c_lon, _c_utc = st.columns(3)
        with _c_lat:
            latitude = st.number_input("Широта", min_value=-90.0, max_value=90.0, value=55.7558, format="%.4f", key="input_latitude")
        with _c_lon:
            longitude = st.number_input("Долгота", min_value=-180.0, max_value=180.0, value=37.6173, format="%.4f", key="input_longitude")
        with _c_utc:
            utc_offset = st.number_input("UTC (ч)", min_value=-12.0, max_value=14.0, value=3.0, format="%.1f", key="input_utc_offset")
    
    # --- Save Profile ---
    st.divider()
    
    if editing_profile:
        c_save, c_cancel = st.columns([2, 1])
        with c_save:
            if st.button("💾 Сохранить изменения", type="primary", use_container_width=True, key="btn_save_profile_changes"):
                on_profile_save(editing_profile)
        with c_cancel:
            if st.button("Отмена", use_container_width=True, key="btn_cancel_edit"):
                state.editing_profile_name = None
                st.rerun()
    else:
        if st.button("💾 Сохранить как профиль", use_container_width=True, key="btn_save_profile"):
            on_profile_save(None)
    
    return {
        "name": name,
        "birth_date": birth_date,
        "birth_time": birth_time,
        "latitude": latitude,
        "longitude": longitude,
        "utc_offset": utc_offset,
        "coord_source": coord_source,
    }


def render_additional_settings_panel(state, on_change: Callable):
    """Render additional settings (house system, zodiac, objects)."""
    with st.expander("⚙️ Дополнительные настройки", expanded=False):
        _c_house, _c_zodiac = st.columns(2)
        with _c_house:
            house_system = st.selectbox(
                "Дома", ["placidus", "koch", "equal", "whole_sign", "porphyry"], index=0,
                key="select_house_system",
            )
        with _c_zodiac:
            zodiac_type_display = st.radio("Зодиак", ["Тропический", "Сидерический"], index=0, key="radio_zodiac")
        zodiac_type = "tropical" if zodiac_type_display == "Тропический" else "sidereal"
        
        ayanamsha = "lahiri"
        if zodiac_type == "sidereal":
            ayanamsha_display = st.selectbox("Аянамша", ["Лахири", "Раман", "Кришнамурти", "Фаган-Брэдли"], index=0, key="select_ayanamsha")
            ayanamsha = {"Лахири": "lahiri", "Раман": "raman", "Кришнамурти": "krishnamurti", "Фаган-Брэдли": "fagan_brady"}[ayanamsha_display]
        
        _o1, _o2 = st.columns(2)
        with _o1:
            include_chiron = st.checkbox("Хирон", key="chk_chiron", on_change=on_change)
            include_fortune = st.checkbox("Part of Fortune", key="chk_fortune", on_change=on_change)
        with _o2:
            include_nodes = st.checkbox("Лунные узлы", key="chk_nodes", on_change=on_change)
            include_angles = st.checkbox("ASC/MC", key="chk_angles", on_change=on_change)
        
        ephe_path = st.text_input("Путь к эфемеридам", value="ephe", key="input_ephe_path")
    
    return {
        "house_system": house_system,
        "zodiac_type": zodiac_type,
        "ayanamsha": ayanamsha,
        "include_chiron": include_chiron,
        "include_nodes": include_nodes,
        "include_fortune": include_fortune,
        "include_angles": include_angles,
        "ephe_path": ephe_path,
    }