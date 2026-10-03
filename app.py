import streamlit as st
import pandas as pd
import json
from datetime import date, time, datetime, timedelta
from datetime import datetime as dt_datetime

from astro_core.chart import build_natal_chart
from astro_core.transits import (
    get_transit_calendar,
    find_transit_events,
    find_transit_periods,
    calculate_transit_positions,
    find_transits_on_date,
)
from astro_core.ephemeris import SWISSEPH_AVAILABLE
from astro_core.constants import (
    DEFAULT_TRANSIT_PLANETS,
    ASPECT_DEFINITIONS,
    get_planet_name_ru,
    get_sign_name_ru,
    get_aspect_name_ru,
    get_object_type_name_ru,
    get_direction_name_ru,
)
from astro_core.profiles import save_profile, load_profile, list_profiles, delete_profile
from astro_core.progressions import (
    calculate_secondary_progressions,
    calculate_solar_arc_progressions,
    find_progression_aspects,
)
from astro_core.chart_svg import (
    render_natal_chart_svg,
    render_transit_chart_svg,
    PLANET_COLORS,
    ASPECT_COLORS,
)
from astro_core.chart_interactive import render_interactive_chart, render_interactive_transit_chart
from astro_core.cities import load_cities, search_cities, get_city_by_name, get_city_display_name
from astro_core.timezone_service import get_utc_offset_hours, get_timezone_info
from astro_core.time_service import datetime_to_jd
from astro_core.display_profiles import (
    list_display_profiles,
    load_display_profile,
    save_display_profile,
    validate_profile,
    ALL_PLANETS,
    ALL_ASPECTS,
    DEFAULT_ORBS,
)
import streamlit.components.v1 as components

# ============================================================
# Настройка страницы и заголовок
# ============================================================

st.set_page_config(page_title="Astro Processor", page_icon="🌟", layout="wide")
st.title("🌟 Astro Processor")
st.markdown("Локальный модульный астрологический процессор")

# Компактные стили
st.markdown(
    """
    <style>
    .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; }
    h1 { font-size: 1.6rem !important; line-height: 1.3 !important; margin-top: 0 !important; padding-top: 0 !important; }
    .stButton > button, .stDownloadButton > button {
        font-size: 0.78rem; padding: 0.3rem 0.5rem; height: auto; line-height: 1.2;
    }
    .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {
        font-size: 0.82rem;
    }
    label { font-size: 0.8rem; }
    /* Убираем лишние боковые отступы у центральной колонки */
    div[data-testid="column"] { padding: 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Проверка Swiss Ephemeris
if not SWISSEPH_AVAILABLE:
    st.error("Swiss Ephemeris is not installed. Please install it with: `py -3.11 -m pip install pyswisseph`")
    st.stop()

# ============================================================
# ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ (сохраняется между запусками)
# ============================================================

if "show_left_panel" not in st.session_state:
    st.session_state["show_left_panel"] = True
if "show_right_panel" not in st.session_state:
    st.session_state["show_right_panel"] = True
if "current_date_nav" not in st.session_state:
    st.session_state["current_date_nav"] = date.today()
if "transit_city_data" not in st.session_state:
    st.session_state["transit_city_data"] = None
if "chart_type" not in st.session_state:
    st.session_state["chart_type"] = "Натальная карта"

# ХРАНИЛИЩЕ ДАННЫХ ПРОФИЛЯ (не зависит от виджетов)
if "profile_data" not in st.session_state:
    st.session_state["profile_data"] = {
        "name": "Иван",
        "birth_date": date(1990, 5, 15),
        "birth_time": time(14, 30),
        "coord_source": "Из города",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset": 3.0,
    }

# -------- СОСТОЯНИЕ ПРОФИЛЯ ОТОБРАЖЕНИЯ (шаг 2.4) --------
if "sel_display_profile_name" not in st.session_state:
    st.session_state["sel_display_profile_name"] = "full"
if "sel_planets" not in st.session_state:
    st.session_state["sel_planets"] = list(ALL_PLANETS)
if "sel_aspects" not in st.session_state:
    st.session_state["sel_aspects"] = list(ALL_ASPECTS)
if "chk_chiron" not in st.session_state:
    st.session_state["chk_chiron"] = True
if "chk_nodes" not in st.session_state:
    st.session_state["chk_nodes"] = True
if "chk_fortune" not in st.session_state:
    st.session_state["chk_fortune"] = True
if "chk_angles" not in st.session_state:
    st.session_state["chk_angles"] = True
for _a in ALL_ASPECTS:
    if f"orb_{_a}" not in st.session_state:
        st.session_state[f"orb_{_a}"] = float(DEFAULT_ORBS[_a])
    if f"acolor_{_a}" not in st.session_state:
        st.session_state[f"acolor_{_a}"] = ASPECT_COLORS.get(_a, "#888888")
for _p in ALL_PLANETS:
    if f"color_{_p}" not in st.session_state:
        st.session_state[f"color_{_p}"] = PLANET_COLORS.get(_p, "#000000")
if "radio_label_mode" not in st.session_state:
    st.session_state["radio_label_mode"] = "symbols"
if "chk_show_aspects" not in st.session_state:
    st.session_state["chk_show_aspects"] = True
if "chk_show_houses" not in st.session_state:
    st.session_state["chk_show_houses"] = True
if "slider_chart_size" not in st.session_state:
    st.session_state["slider_chart_size"] = 800
if "slider_dot_size" not in st.session_state:
    st.session_state["slider_dot_size"] = 5

# Значения по умолчанию (защита, если панель свёрнута)
calculate_button = False
calculate_transits_button = False
calculate_progressions_button = False
selected_planets = []
selected_aspects = []
transit_mode = "Быстрый (по дням)"
transit_date_option = "Диапазон дат"
transit_single_date = date.today()
transit_start_date = date.today()
transit_end_date = date.today() + timedelta(days=7)

# -------- КЛЮЧИ ПРОФИЛЯ ОТОБРАЖЕНИЯ (Правка A) --------
if "display_profile_selector" not in st.session_state:
    st.session_state["display_profile_selector"] = "full"
if "flag_recalculate_chart" not in st.session_state:
    st.session_state["flag_recalculate_chart"] = False
if "display_profile_error" not in st.session_state:
    st.session_state["display_profile_error"] = None

# -------- ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ для переменных левой панели --------
# Защита от ошибки, если панель свёрнута, но сработал автопересчёт карты.
name = st.session_state.get("input_name", "Иван")
birth_date = st.session_state.get("input_birth_date", date(1990, 5, 15))
birth_time = st.session_state.get("input_birth_time", time(14, 30))
latitude = st.session_state.get("profile_data", {}).get("latitude", 0.0)
longitude = st.session_state.get("profile_data", {}).get("longitude", 0.0)
utc_offset = st.session_state.get("profile_data", {}).get("utc_offset", 0.0)
house_system = "placidus"
zodiac_type = "tropical"
ayanamsha = "lahiri"
include_chiron = st.session_state.get("chk_chiron", True)
include_nodes = st.session_state.get("chk_nodes", True)
include_fortune = st.session_state.get("chk_fortune", True)
include_angles = st.session_state.get("chk_angles", True)
ephe_path = "ephe"

show_left = st.session_state["show_left_panel"]
show_right = st.session_state["show_right_panel"]

# ============================================================
# Кнопки сворачивания панелей (всегда видны вверху)
# ============================================================

tg1, tg2, tg3 = st.columns([1, 8, 1])
with tg1:
    if st.button("◀ Скрыть" if show_left else "▶ Показать", key="btn_toggle_left", use_container_width=True):
        st.session_state["show_left_panel"] = not show_left
with tg3:
    if st.button("Скрыть ▶" if show_right else "Показать ◀", key="btn_toggle_right", use_container_width=True):
        st.session_state["show_right_panel"] = not show_right

# Перечитываем после возможного изменения
show_left = st.session_state["show_left_panel"]
show_right = st.session_state["show_right_panel"]

# ============================================================
# Создание колонок: ВСЕГДА три колонки (структура не меняется!)
# Это гарантирует, что виджеты в центре не сбрасываются.
# Когда панель скрыта, её ширина минимальна.
# ============================================================

left_w = 1.0 if show_left else 0.001
right_w = 1.0 if show_right else 0.001
col_left, col_center, col_right = st.columns([left_w, 3.6, right_w])

# ============================================================
# ЛЕВАЯ ПАНЕЛЬ: входные данные
# ============================================================

# Функция-колбэк применения профиля отображения (Правка B).
# Передаётся в кнопку через on_click, поэтому выполняется ДО создания
# виджетов и может безопасно менять любые ключи session_state.
def apply_display_profile_callback():
    try:
        profile_name = st.session_state.get("display_profile_selector", "full")
        _prof = load_display_profile(profile_name)
        _objs = _prof.get("objects", {})
        _asps = _prof.get("aspects", {})
        _app = _prof.get("appearance", {})

        # Объекты (чекбоксы в «Дополнительных настройках»)
        st.session_state["chk_chiron"] = bool(_objs.get("Chiron", True))
        st.session_state["chk_nodes"] = bool(_objs.get("LunarNodes", True))
        st.session_state["chk_fortune"] = bool(_objs.get("PartOfFortune", True))
        st.session_state["chk_angles"] = bool(_objs.get("Angles", True))

        # Планеты и аспекты
        st.session_state["sel_planets"] = [p for p in ALL_PLANETS if _objs.get(p, True)]
        st.session_state["sel_aspects"] = [a for a in ALL_ASPECTS if _asps.get(a, {}).get("enabled", True)]
        for _a in ALL_ASPECTS:
            st.session_state[f"orb_{_a}"] = float(_asps.get(_a, {}).get("orb", DEFAULT_ORBS[_a]))

        # Внешний вид
        st.session_state["radio_label_mode"] = _app.get("label_mode", "symbols")
        st.session_state["chk_show_aspects"] = bool(_app.get("show_aspect_lines", True))
        st.session_state["chk_show_houses"] = bool(_app.get("show_houses", True))
        st.session_state["slider_chart_size"] = int(_app.get("chart_size", 800))
        st.session_state["slider_dot_size"] = int(_app.get("planet_dot_size", 5))
        for _p in ALL_PLANETS:
            if _p in _app.get("planet_colors", {}):
                st.session_state[f"color_{_p}"] = _app["planet_colors"][_p]
        for _a in ALL_ASPECTS:
            if _a in _app.get("aspect_colors", {}):
                st.session_state[f"acolor_{_a}"] = _app["aspect_colors"][_a]

        # Запомнить имя профиля и заказать автопересчёт карты
        st.session_state["sel_display_profile_name"] = profile_name
        st.session_state["flag_recalculate_chart"] = True
        st.session_state["display_profile_error"] = None
    except Exception as error:
        st.session_state["display_profile_error"] = str(error)


if show_left:
    with col_left:
        # -------- ПРОФИЛИ РОЖДЕНИЯ --------
        st.markdown("##### 👤 Профили")

        profiles = list_profiles()
        profile_names = [p.get("name", "Без имени") for p in profiles]

        if profile_names:
            selected_profile_name = st.selectbox(
                "Выбрать профиль", options=profile_names, index=None,
                placeholder="— выберите профиль —",
            )
        else:
            st.info("Профилей пока нет.")
            selected_profile_name = None

        editing_profile = st.session_state.get("editing_profile")
        if editing_profile:
            st.info(f"✏️ Редактируется: {editing_profile}")

        c_load, c_edit = st.columns(2)
        with c_load:
            load_profile_button = st.button("📂 Загрузить", disabled=(selected_profile_name is None), use_container_width=True)
        with c_edit:
            edit_profile_button = st.button("✏️ Редакт.", disabled=(selected_profile_name is None), use_container_width=True)

        confirm_delete = st.checkbox("Подтвердить удаление", value=False, key="confirm_delete")
        delete_profile_button = st.button(
            "🗑️ Удалить", disabled=(selected_profile_name is None or not confirm_delete), use_container_width=True
        )

        def _apply_profile_to_state(profile):
            name_val = profile.get("name", "")
            date_val = datetime.strptime(profile["date"], "%Y-%m-%d").date() if "date" in profile else date.today()
            time_val = datetime.strptime(profile["time"], "%H:%M").time() if "time" in profile else time(0, 0)
            lat_val = float(profile.get("latitude", 0.0))
            lon_val = float(profile.get("longitude", 0.0))
            utc_val = float(profile.get("utc_offset_hours", 0.0))

            st.session_state["profile_data"] = {
                "name": name_val, "birth_date": date_val, "birth_time": time_val,
                "coord_source": "Вручную", "latitude": lat_val, "longitude": lon_val, "utc_offset": utc_val,
            }
            st.session_state["input_name"] = name_val
            st.session_state["input_birth_date"] = date_val
            st.session_state["input_birth_time"] = time_val
            st.session_state["coord_source"] = "Вручную"
            st.session_state["input_latitude"] = lat_val
            st.session_state["input_longitude"] = lon_val
            st.session_state["input_utc_offset"] = utc_val

        if load_profile_button and selected_profile_name:
            try:
                profile = load_profile(selected_profile_name)
                _apply_profile_to_state(profile)
                st.session_state.pop("editing_profile", None)
                st.rerun()
            except Exception as error:
                st.error(f"Ошибка загрузки профиля: {error}")

        if edit_profile_button and selected_profile_name:
            try:
                profile = load_profile(selected_profile_name)
                _apply_profile_to_state(profile)
                st.session_state["editing_profile"] = selected_profile_name
                st.rerun()
            except Exception as error:
                st.error(f"Ошибка загрузки профиля: {error}")

        if delete_profile_button and selected_profile_name:
            try:
                delete_profile(selected_profile_name)
                st.session_state["confirm_delete"] = False
                if st.session_state.get("editing_profile") == selected_profile_name:
                    st.session_state.pop("editing_profile", None)
                st.rerun()
            except Exception as error:
                st.error(f"Ошибка удаления профиля: {error}")

        st.divider()

        # -------- ДАННЫЕ РОЖДЕНИЯ --------
        _pd = st.session_state.get("profile_data", {})
        if _pd:
            if "input_name" not in st.session_state:
                st.session_state["input_name"] = _pd.get("name", "Иван")
            if "input_birth_date" not in st.session_state:
                st.session_state["input_birth_date"] = _pd.get("birth_date", date(1990, 5, 15))
            if "input_birth_time" not in st.session_state:
                st.session_state["input_birth_time"] = _pd.get("birth_time", time(14, 30))
            if "coord_source" not in st.session_state:
                st.session_state["coord_source"] = _pd.get("coord_source", "Из города")
            if "input_latitude" not in st.session_state:
                st.session_state["input_latitude"] = _pd.get("latitude", 55.7558)
            if "input_longitude" not in st.session_state:
                st.session_state["input_longitude"] = _pd.get("longitude", 37.6173)
            if "input_utc_offset" not in st.session_state:
                st.session_state["input_utc_offset"] = _pd.get("utc_offset", 3.0)

        st.markdown("##### 📅 Данные рождения")

        name = st.text_input("Имя", key="input_name")
        birth_date = st.date_input(
            "Дата рождения", value=date(1990, 5, 15),
            min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key="input_birth_date",
        )
        birth_time = st.time_input("Время рождения", value=time(14, 30), key="input_birth_time")

        if "chart_result" in st.session_state:
            _res = st.session_state["chart_result"]
            with st.expander("🔢 Технические данные карты", expanded=False):
                st.write(f"**Дата:** {_res['birth']['date']}")
                st.write(f"**Время:** {_res['birth']['time']}")
                st.write(f"**UTC:** {_res['utc_datetime']}")
                st.write(f"**Julian Day:** {_res['julian_day']}")

        # -------- ГОРОД РОЖДЕНИЯ --------
        st.markdown("##### 🏙️ Город рождения")

        coord_source = st.radio(
            "Источник координат", ["Из города", "Вручную"],
            index=0, key="coord_source", horizontal=True,
        )

        latitude, longitude, utc_offset = 0.0, 0.0, 0.0

        if coord_source == "Из города":
            city_query = st.text_input("Поиск города", value="", key="city_query")
            if city_query.strip():
                found_cities = search_cities(city_query, limit=10)
            else:
                found_cities = load_cities()[:10]

            if found_cities:
                city_options = [get_city_display_name(c) for c in found_cities]
                selected_city_display = st.selectbox("Город", options=city_options, index=0, key="selected_city")

                selected_city = None
                for c in found_cities:
                    if get_city_display_name(c) == selected_city_display:
                        selected_city = c
                        break

                if selected_city:
                    latitude = selected_city["latitude"]
                    longitude = selected_city["longitude"]
                    timezone_name = selected_city.get("timezone", "")

                    if timezone_name:
                        try:
                            birth_dt_for_tz = dt_datetime.combine(birth_date, birth_time)
                            tz_info = get_timezone_info(timezone_name, birth_dt_for_tz)
                            utc_offset = tz_info["utc_offset"]
                        except ValueError:
                            utc_offset = 0.0

                    st.caption(f"📍 {latitude:.4f}, {longitude:.4f} · {timezone_name} · UTC{utc_offset:+.2f}")
                else:
                    latitude, longitude, utc_offset = 0.0, 0.0, 0.0
            else:
                st.warning("Город не найден.")
        else:
            latitude = st.number_input("Широта", min_value=-90.0, max_value=90.0, value=55.7558, format="%.4f", key="input_latitude")
            longitude = st.number_input("Долгота", min_value=-180.0, max_value=180.0, value=37.6173, format="%.4f", key="input_longitude")
            utc_offset = st.number_input("Смещение UTC (часы)", min_value=-12.0, max_value=14.0, value=3.0, format="%.1f", key="input_utc_offset")

        st.session_state["profile_data"].update({
            "name": name, "birth_date": birth_date, "birth_time": birth_time,
            "coord_source": coord_source, "latitude": latitude, "longitude": longitude, "utc_offset": utc_offset,
        })

        # -------- СОХРАНЕНИЕ ПРОФИЛЯ РОЖДЕНИЯ --------
        editing_profile = st.session_state.get("editing_profile")

        if editing_profile:
            c_save, c_cancel = st.columns([2, 1])
            with c_save:
                save_profile_button = st.button("💾 Сохранить изменения", type="primary", use_container_width=True)
            with c_cancel:
                cancel_edit_button = st.button("Отмена", use_container_width=True)

            if cancel_edit_button:
                st.session_state.pop("editing_profile", None)
                st.rerun()
        else:
            save_profile_button = st.button("💾 Сохранить как профиль", use_container_width=True)

        if save_profile_button:
            if not name.strip():
                st.warning("Введите имя перед сохранением.")
            else:
                new_name = name.strip()
                profile_data = {
                    "name": new_name,
                    "date": birth_date.strftime("%Y-%m-%d"),
                    "time": birth_time.strftime("%H:%M"),
                    "latitude": latitude,
                    "longitude": longitude,
                    "utc_offset_hours": utc_offset,
                }

                try:
                    save_profile(profile_data)
                    if editing_profile and new_name != editing_profile:
                        delete_profile(editing_profile)
                        st.session_state.pop("editing_profile", None)
                    elif editing_profile:
                        st.session_state.pop("editing_profile", None)
                    st.rerun()
                except Exception as error:
                    st.error(f"Ошибка сохранения профиля: {error}")

        st.divider()

        # -------- ПРОФИЛЬ ОТОБРАЖЕНИЯ (поднят выше — Правка B) --------
        st.markdown("##### 🎨 Профиль отображения")

        display_profiles_list = list_display_profiles()
        display_profile_options = [p.get("name", "") for p in display_profiles_list]
        if not display_profile_options:
            display_profile_options = ["full"]

        selected_display_profile = st.selectbox(
            "Профиль", options=display_profile_options, key="display_profile_selector",
        )

        new_display_profile_name = st.text_input(
            "Имя для сохранения",
            value=st.session_state.get("sel_display_profile_name", "full"),
            key="new_display_profile_name",
        )

        dp_c1, dp_c2 = st.columns(2)
        with dp_c1:
            st.button(
                "📥 Применить",
                key="btn_apply_display_profile",
                on_click=apply_display_profile_callback,
                use_container_width=True,
            )
        with dp_c2:
            save_display_profile_btn = st.button("💾 Сохранить", use_container_width=True)

        if st.session_state.get("display_profile_error"):
            st.error(f"Ошибка применения профиля отображения: {st.session_state['display_profile_error']}")
            st.session_state["display_profile_error"] = None

        if save_display_profile_btn:
            _dp_name = (new_display_profile_name or "").strip()
            if not _dp_name:
                st.warning("Введите имя профиля отображения перед сохранением.")
            else:
                _new_profile = {
                    "name": _dp_name,
                    "description": "Пользовательский профиль отображения",
                    "objects": {},
                    "aspects": {},
                    "appearance": {},
                }

                _cur_planets = st.session_state.get("sel_planets", [])
                for _p in ALL_PLANETS:
                    _new_profile["objects"][_p] = _p in _cur_planets
                _new_profile["objects"]["Chiron"] = bool(st.session_state.get("chk_chiron", True))
                _new_profile["objects"]["LunarNodes"] = bool(st.session_state.get("chk_nodes", True))
                _new_profile["objects"]["PartOfFortune"] = bool(st.session_state.get("chk_fortune", True))
                _new_profile["objects"]["Angles"] = bool(st.session_state.get("chk_angles", True))

                _cur_aspects = st.session_state.get("sel_aspects", [])
                for _a in ALL_ASPECTS:
                    _new_profile["aspects"][_a] = {
                        "enabled": _a in _cur_aspects,
                        "orb": float(st.session_state.get(f"orb_{_a}", DEFAULT_ORBS[_a])),
                    }

                _new_profile["appearance"] = {
                    "label_mode": st.session_state.get("radio_label_mode", "symbols"),
                    "show_houses": bool(st.session_state.get("chk_show_houses", True)),
                    "show_aspect_lines": bool(st.session_state.get("chk_show_aspects", True)),
                    "chart_size": int(st.session_state.get("slider_chart_size", 800)),
                    "planet_dot_size": int(st.session_state.get("slider_dot_size", 5)),
                    "planet_colors": {
                        p: st.session_state.get(f"color_{p}", PLANET_COLORS.get(p, "#000000"))
                        for p in ALL_PLANETS
                    },
                    "aspect_colors": {
                        a: st.session_state.get(f"acolor_{a}", ASPECT_COLORS.get(a, "#888888"))
                        for a in ALL_ASPECTS
                    },
                }

                _errors = validate_profile(_new_profile)
                if _errors:
                    for _e in _errors:
                        st.error(_e)
                else:
                    try:
                        save_display_profile(_new_profile)
                        st.session_state["sel_display_profile_name"] = _dp_name
                        st.session_state["display_profile_selector"] = _dp_name
                        st.rerun()
                    except Exception as error:
                        st.error(f"Ошибка сохранения профиля отображения: {error}")

        # Редактор профиля отображения
        with st.expander("Настроить объекты, аспекты и внешний вид"):
            display_planets = st.multiselect(
                "Планеты", options=list(ALL_PLANETS),
                format_func=get_planet_name_ru, key="sel_planets",
            )
            st.caption("Хирон, узлы, Part of Fortune и ASC/MC — чекбоксы в «Дополнительных настройках» ниже.")

            display_aspects = st.multiselect(
                "Аспекты", options=list(ALL_ASPECTS),
                format_func=get_aspect_name_ru, key="sel_aspects",
            )

            st.markdown("**Орбы аспектов (°)**")
            orb_c1, orb_c2 = st.columns(2)
            for _idx, _aspect_name in enumerate(ALL_ASPECTS):
                _col = orb_c1 if _idx % 2 == 0 else orb_c2
                with _col:
                    st.number_input(
                        get_aspect_name_ru(_aspect_name),
                        min_value=0.0, max_value=30.0, step=0.5,
                        key=f"orb_{_aspect_name}",
                    )

            st.divider()
            st.markdown("**Внешний вид**")

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

            st.markdown("**Цвета планет**")
            for _row_start in range(0, len(ALL_PLANETS), 2):
                pc1, pc2 = st.columns(2)
                _planet_a = ALL_PLANETS[_row_start]
                with pc1:
                    st.color_picker(get_planet_name_ru(_planet_a), key=f"color_{_planet_a}")
                if _row_start + 1 < len(ALL_PLANETS):
                    _planet_b = ALL_PLANETS[_row_start + 1]
                    with pc2:
                        st.color_picker(get_planet_name_ru(_planet_b), key=f"color_{_planet_b}")

            st.markdown("**Цвета аспектов**")
            for _row_start in range(0, len(ALL_ASPECTS), 2):
                ac1, ac2 = st.columns(2)
                _aspect_a = ALL_ASPECTS[_row_start]
                with ac1:
                    st.color_picker(get_aspect_name_ru(_aspect_a), key=f"acolor_{_aspect_a}")
                if _row_start + 1 < len(ALL_ASPECTS):
                    _aspect_b = ALL_ASPECTS[_row_start + 1]
                    with ac2:
                        st.color_picker(get_aspect_name_ru(_aspect_b), key=f"acolor_{_aspect_b}")

        # -------- ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ (свёрнуты — Правка B) --------
        with st.expander("⚙️ Дополнительные настройки", expanded=False):
            house_system = st.selectbox(
                "Система домов", ["placidus", "koch", "equal", "whole_sign", "porphyry"], index=0,
            )

            zodiac_type_display = st.radio("Тип зодиака", ["Тропический", "Сидерический"], index=0)
            zodiac_type = "tropical" if zodiac_type_display == "Тропический" else "sidereal"

            ayanamsha = "lahiri"
            if zodiac_type == "sidereal":
                ayanamsha_display = st.selectbox("Система аянамши", ["Лахири", "Раман", "Кришнамурти", "Фаган-Брэдли"], index=0)
                ayanamsha = {"Лахири": "lahiri", "Раман": "raman", "Кришнамурти": "krishnamurti", "Фаган-Брэдли": "fagan_brady"}[ayanamsha_display]

            include_chiron = st.checkbox("Хирон", key="chk_chiron")
            include_nodes = st.checkbox("Лунные узлы", key="chk_nodes")
            include_fortune = st.checkbox("Part of Fortune", key="chk_fortune")
            include_angles = st.checkbox("ASC/MC", key="chk_angles")

            ephe_path = st.text_input("Путь к эфемеридам", value="ephe")

        calculate_button = st.button("🔮 Рассчитать карту", type="primary", use_container_width=True)
        
    # ============================================================
    # ПРАВАЯ ПАНЕЛЬ: управление транзитами
    # ============================================================

    if show_right:
        with col_right:
            st.markdown("##### 🔄 Управление транзитами")

            if "chart_result" not in st.session_state:
                st.info("Сначала рассчитайте натальную карту в левой панели — транзиты строятся относительно неё.")
            else:
                transit_mode = st.radio(
                    "Режим",
                    ["Быстрый (по дням)", "Точный (с временем аспектов)", "Периоды активности"],
                    index=0,
                )

                # Опции фильтра — только планеты из профиля рассчитанной натальной карты (шаг 2.5)
                planet_options = list(
                    st.session_state.get("settings", {}).get("enabled_planets", DEFAULT_TRANSIT_PLANETS)
                )
                selected_planets = st.multiselect(
                    "Транзитные планеты (пусто = все)", options=planet_options,
                    format_func=get_planet_name_ru, default=[],
                )

                aspect_options = [a["name"] for a in ASPECT_DEFINITIONS]
                selected_aspects = st.multiselect(
                    "Аспекты (пусто = все)", options=aspect_options,
                    format_func=get_aspect_name_ru, default=[],
                )

                st.divider()
                st.markdown("##### 📅 Дата транзита")

                def _shift_transit_date(days):
                    st.session_state["current_date_nav"] += timedelta(days=days)

                nav1, nav2 = st.columns(2)
                with nav1:
                    st.button("⏪ -1 мес", on_click=_shift_transit_date, args=(-30,), use_container_width=True)
                    st.button("◀️ -1 день", on_click=_shift_transit_date, args=(-1,), use_container_width=True)
                with nav2:
                    st.button("+1 день ▶️", on_click=_shift_transit_date, args=(1,), use_container_width=True)
                    st.button("+1 мес ⏩", on_click=_shift_transit_date, args=(30,), use_container_width=True)

                st.date_input("Дата транзита", key="current_date_nav")

                st.divider()
                st.markdown("##### 🏙️ Город транзита")

                transit_location_mode = st.radio(
                    "Привязка к городу", ["Без города", "Выбрать город"],
                    index=0, key="transit_location_mode",
                )

                if transit_location_mode == "Выбрать город":
                    transit_city_query = st.text_input("Поиск города транзита", value="", key="transit_city_query")
                    if transit_city_query.strip():
                        found_transit_cities = search_cities(transit_city_query, limit=10)
                    else:
                        found_transit_cities = load_cities()[:10]

                    if found_transit_cities:
                        transit_city_options = [get_city_display_name(c) for c in found_transit_cities]
                        selected_transit_city_display = st.selectbox(
                            "Город транзита", options=transit_city_options, index=0, key="selected_transit_city",
                        )

                        _chosen_tc = None
                        for c in found_transit_cities:
                            if get_city_display_name(c) == selected_transit_city_display:
                                _chosen_tc = c
                                break

                        st.session_state["transit_city_data"] = _chosen_tc
                        if _chosen_tc:
                            st.caption(f"📍 {_chosen_tc['name']}, {_chosen_tc['country']}")
                        else:
                            st.warning("Город не найден.")
                            st.session_state["transit_city_data"] = None
                    else:
                        st.session_state["transit_city_data"] = None
                else:
                    st.session_state["transit_city_data"] = None

                st.divider()

                transit_date_option = st.radio("Тип периода", ["Одна дата", "Диапазон дат"], index=1)

                if transit_date_option == "Одна дата":
                    transit_single_date = st.date_input(
                        "Дата транзитов", value=date.today(),
                        min_value=date(1900, 1, 1), max_value=date(2100, 12, 31),
                    )
                else:
                    transit_start_date = st.date_input(
                        "Дата начала", value=date.today(),
                        min_value=date(1900, 1, 1), max_value=date(2100, 12, 31),
                    )
                    transit_end_date = st.date_input(
                        "Дата конца", value=date.today() + timedelta(days=7),
                        min_value=date(1900, 1, 1), max_value=date(2100, 12, 31),
                    )

                st.divider()

                calculate_transits_button = st.button("🔮 Рассчитать транзиты", type="primary", use_container_width=True)

# ============================================================
# ОБРАБОТЧИК: расчёт натальной карты
# ============================================================

need_recalc = st.session_state.get("flag_recalculate_chart", False)
if calculate_button or need_recalc:
    st.session_state["flag_recalculate_chart"] = False
    birth = {
        "name": name,
        "date": birth_date.strftime("%Y-%m-%d"),
        "time": birth_time.strftime("%H:%M"),
        "latitude": latitude,
        "longitude": longitude,
        "utc_offset_hours": utc_offset,
    }

    # Настройки отображения из профиля (шаг 2.4):
    # какие планеты и аспекты участвуют в расчёте, какие орбы используются.
    enabled_planets_ui = st.session_state.get("sel_planets", list(ALL_PLANETS))
    enabled_aspects_ui = st.session_state.get("sel_aspects", list(ALL_ASPECTS))
    orbs_ui = {
        a: float(st.session_state.get(f"orb_{a}", DEFAULT_ORBS[a]))
        for a in enabled_aspects_ui
    }

    settings = {
        "house_system": house_system,
        "include_chiron": include_chiron,
        "include_nodes": include_nodes,
        "include_part_of_fortune": include_fortune,
        "include_angles": include_angles,
        "ephe_path": ephe_path if ephe_path else None,
        "zodiac": zodiac_type,
        "ayanamsha": ayanamsha,
        "enabled_planets": list(enabled_planets_ui),
        "enabled_aspects": list(enabled_aspects_ui),
        "orbs": orbs_ui,
    }

    try:
        result = build_natal_chart(birth, settings)
        st.session_state["chart_result"] = result
        st.session_state["birth"] = birth
        st.session_state["settings"] = settings
        st.session_state.pop("transit_result", None)
        st.session_state.pop("transit_mode_used", None)
        st.session_state.pop("transit_period", None)
        st.rerun()
    except Exception as error:
        st.error(f"Ошибка расчёта карты: {error}")

# ============================================================
# ОБРАБОТЧИК: расчёт транзитов
# ============================================================

if calculate_transits_button and "chart_result" in st.session_state:
    natal_objects = st.session_state["chart_result"]["objects"]

    if transit_date_option == "Одна дата":
        start_date = transit_single_date.strftime("%Y-%m-%d")
        end_date = transit_single_date.strftime("%Y-%m-%d")
    else:
        start_date = transit_start_date.strftime("%Y-%m-%d")
        end_date = transit_end_date.strftime("%Y-%m-%d")

    transit_settings = dict(st.session_state["settings"])
    # Ограничиваем транзитные планеты планетами натальной карты (шаг 2.5):
    # транзиты строятся только для планет, включённых в профиль на момент расчёта карты.
    if "enabled_planets" in transit_settings:
        transit_settings["transit_planets"] = list(transit_settings["enabled_planets"])
    filter_planets = selected_planets if selected_planets else None
    filter_aspects = selected_aspects if selected_aspects else None

    with st.spinner("Расчёт транзитов... Пожалуйста, подождите."):
        try:
            if "Периоды активности" in transit_mode:
                periods = find_transit_periods(natal_objects, start_date, end_date, transit_settings, filter_planets=filter_planets, filter_aspects=filter_aspects)
                st.session_state["transit_result"] = periods
                st.session_state["transit_mode_used"] = "periods"
                st.session_state["transit_period"] = (start_date, end_date)
            elif "Точный" in transit_mode:
                events = find_transit_events(natal_objects, start_date, end_date, transit_settings, filter_planets=filter_planets, filter_aspects=filter_aspects)
                st.session_state["transit_result"] = events
                st.session_state["transit_mode_used"] = "precise"
                st.session_state["transit_period"] = (start_date, end_date)
            else:
                calendar = get_transit_calendar(natal_objects, start_date, end_date, transit_settings, filter_planets=filter_planets, filter_aspects=filter_aspects)
                st.session_state["transit_result"] = calendar
                st.session_state["transit_mode_used"] = "calendar"
                st.session_state["transit_period"] = (start_date, end_date)
        except Exception as error:
            st.error(f"Ошибка расчёта транзитов: {error}")

# ============================================================
# ЦЕНТРАЛЬНАЯ ПАНЕЛЬ: результат карты
# ============================================================

with col_center:
    if "chart_result" not in st.session_state:
        st.info("Введите данные рождения в левой панели и нажмите «Рассчитать карту».")
    else:
        result = st.session_state["chart_result"]

        # Заголовок карты (возвращён)
        chart_name = result["birth"].get("name", "Chart")
        st.subheader(f"Натальная карта: {chart_name}")

        if result.get("warnings"):
            with st.expander("Предупреждения", expanded=False):
                for warning in result["warnings"]:
                    st.warning(warning)

        tab_chart, tab_objects, tab_houses, tab_aspects, tab_progressions, tab_json = st.tabs(
            ["🌌 Карта", "Объекты", "Дома", "Аспекты", "🔄 Прогрессии", "JSON"]
        )

        # ------------------------------------------------
        # Вкладка: Карта
        # ------------------------------------------------
        with tab_chart:
            # Тип карты: индекс вычисляется из сохранённого значения,
            # чтобы выбранный тип НЕ сбрасывался при скрытии/показе панелей
            _saved_chart_type_options = ["Натальная карта", "Транзитная карта"]
            _saved_chart_type = st.session_state.get("chart_type", "Натальная карта")
            _saved_chart_type_index = _saved_chart_type_options.index(_saved_chart_type) if _saved_chart_type in _saved_chart_type_options else 0

            chart_type = st.radio(
                "Тип карты",
                _saved_chart_type_options,
                index=_saved_chart_type_index,
                key="chart_type"
            )

            # Внешний вид берётся из профиля отображения
            # (левая панель, секция «🎨 Профиль отображения», шаг 2.4)
            chart_size = st.session_state.get("slider_chart_size", 800)
            label_mode = st.session_state.get("radio_label_mode", "symbols")
            show_aspects = st.session_state.get("chk_show_aspects", True)
            show_houses_ui = st.session_state.get("chk_show_houses", True)
            dot_size_ui = st.session_state.get("slider_dot_size", 5)
            planet_colors_ui = {
                p: st.session_state.get(f"color_{p}", PLANET_COLORS.get(p, "#000000"))
                for p in ALL_PLANETS
            }
            aspect_colors_ui = {
                a: st.session_state.get(f"acolor_{a}", ASPECT_COLORS.get(a, "#888888"))
                for a in ALL_ASPECTS
            }

            if chart_type == "Натальная карта":
                interactive_html = render_interactive_chart(
                    result, size=chart_size, show_aspects=show_aspects, label_mode=label_mode,
                    show_houses=show_houses_ui, planet_dot_size=dot_size_ui,
                    planet_colors=planet_colors_ui, aspect_colors=aspect_colors_ui,
                )
                components.html(interactive_html, height=chart_size + 60, scrolling=True)
                st.caption("💡 Колесо мыши — зум, зажать и двигать — перетаскивание. Внешний вид настраивается в «🎨 Профиле отображения» слева.")

                static_svg = render_natal_chart_svg(
                    result, size=chart_size, show_aspects=show_aspects, label_mode=label_mode,
                    show_houses=show_houses_ui, planet_dot_size=dot_size_ui,
                    planet_colors=planet_colors_ui, aspect_colors=aspect_colors_ui,
                )
                st.download_button("📥 Скачать карту (SVG)", data=static_svg, file_name="natal_chart.svg", mime="image/svg+xml")
            else:
                # Транзитная карта (дата и город берутся из правой панели через session_state)
                transit_date_for_chart = st.session_state["current_date_nav"]
                transit_city = st.session_state.get("transit_city_data")

                transit_houses = None
                transit_additional_points = None

                if transit_city is not None:
                    try:
                        transit_tz_name = transit_city.get("timezone", "")
                        if transit_tz_name:
                            transit_dt_for_tz = dt_datetime.combine(transit_date_for_chart, time(12, 0))
                            transit_utc_offset_hours = get_utc_offset_hours(transit_tz_name, transit_dt_for_tz)
                        else:
                            transit_utc_offset_hours = 0.0

                        natal_settings_for_ephe = st.session_state.get("settings", {})
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

                        transit_chart_result = build_natal_chart(transit_chart_birth, transit_chart_settings)
                        transit_houses = transit_chart_result.get("houses", [])
                        transit_additional_points = transit_chart_result.get("additional_points", [])
                    except Exception as e:
                        st.warning(f"Не удалось рассчитать дома транзита для города: {e}")

                try:
                    natal_utc_offset = st.session_state.get("birth", {}).get("utc_offset_hours", 0.0)
                    transit_dt = datetime.combine(transit_date_for_chart, time(12, 0))
                    transit_utc_dt = transit_dt - timedelta(hours=natal_utc_offset)
                    transit_jd = datetime_to_jd(transit_utc_dt)

                    transit_settings = {"include_chiron": False, "include_nodes": False}
                    transit_planets_list, _ = calculate_transit_positions(transit_jd, transit_settings)

                    if selected_planets:
                        transit_planets_list = [p for p in transit_planets_list if p["name"] in selected_planets]

                    transit_chart_settings = dict(result.get("settings", {}))
                    if selected_aspects:
                        transit_chart_settings["enabled_aspects"] = list(selected_aspects)

                    natal_objects = result.get("objects", [])
                    transit_aspects_list = find_transits_on_date(natal_objects, transit_planets_list, transit_chart_settings)

                    transit_svg = render_transit_chart_svg(
                        result, transit_planets_list, transit_aspects_list,
                        size=chart_size, label_mode=label_mode, show_aspects=show_aspects,
                        transit_houses=transit_houses, transit_additional_points=transit_additional_points,
                        show_houses=show_houses_ui, planet_dot_size=dot_size_ui,
                        planet_colors=planet_colors_ui, aspect_colors=aspect_colors_ui,
                    )

                    interactive_transit_html = render_interactive_transit_chart(
                        result, transit_planets_list, transit_aspects_list,
                        size=chart_size, label_mode=label_mode, show_aspects=show_aspects,
                        transit_houses=transit_houses, transit_additional_points=transit_additional_points,
                        show_houses=show_houses_ui, planet_dot_size=dot_size_ui,
                        planet_colors=planet_colors_ui, aspect_colors=aspect_colors_ui,
                    )

                    components.html(interactive_transit_html, height=chart_size + 60, scrolling=True)

                    transit_city_note = ""
                    if transit_city is not None:
                        transit_city_note = f" Город транзита: {transit_city['name']}. Зелёные линии — дома транзита."

                    st.caption(f"📅 Транзиты на {transit_date_for_chart.strftime('%d.%m.%Y')}. Синий — натальные, зелёный — транзитные.{transit_city_note}")

                    st.download_button(
                        "📥 Скачать транзитную карту (SVG)", data=transit_svg,
                        file_name=f"transit_chart_{transit_date_for_chart.strftime('%Y%m%d')}.svg", mime="image/svg+xml",
                    )
                except Exception as e:
                    st.error(f"Ошибка расчёта транзитной карты: {e}")
       
        # ------------------------------------------------
        # Вкладка: Объекты
        # ------------------------------------------------
        with tab_objects:
            objects_data = []

            for p in result.get("planets", []):
                objects_data.append({
                    "Тип": get_object_type_name_ru(p.get("type", "planet")),
                    "Название": get_planet_name_ru(p["name"]),
                    "Знак": get_sign_name_ru(p["sign"]),
                    "Градус в знаке": round(p["degree_in_sign"], 2),
                    "Долгота": round(p["longitude"], 2),
                    "Дом": p.get("house", "-"),
                    "Ретроград": "Да" if p.get("retrograde") else "Нет",
                })

            for p in result.get("additional_points", []):
                objects_data.append({
                    "Тип": get_object_type_name_ru(p.get("type", "point")),
                    "Название": get_planet_name_ru(p["name"]),
                    "Знак": get_sign_name_ru(p["sign"]),
                    "Градус в знаке": round(p["degree_in_sign"], 2),
                    "Долгота": round(p["longitude"], 2),
                    "Дом": p.get("house", "-"),
                    "Ретроград": "-",
                })

            if objects_data:
                st.dataframe(pd.DataFrame(objects_data), use_container_width=True, hide_index=True)
            else:
                st.info("Нет данных об объектах.")

        # ------------------------------------------------
        # Вкладка: Дома
        # ------------------------------------------------
        with tab_houses:
            houses_data = []

            for h in result.get("houses", []):
                houses_data.append({
                    "Дом": h["house"],
                    "Знак": get_sign_name_ru(h["sign"]),
                    "Градус в знаке": round(h["degree_in_sign"], 2),
                    "Долгота": round(h["longitude"], 2),
                })

            if houses_data:
                st.dataframe(pd.DataFrame(houses_data), use_container_width=True, hide_index=True)
            else:
                st.info("Нет данных о домах.")

        # ------------------------------------------------
        # Вкладка: Аспекты
        # ------------------------------------------------
        with tab_aspects:
            aspects_data = []

            for a in result.get("aspects", []):
                aspects_data.append({
                    "Точка A": get_planet_name_ru(a["point_a"]),
                    "Точка B": get_planet_name_ru(a["point_b"]),
                    "Аспект": get_aspect_name_ru(a["aspect"]),
                    "Угол": round(a["angle"], 2),
                    "Орб": round(a["orb"], 2),
                    "Макс. орб": a["max_orb"],
                    "Сила": round(a["strength"], 2),
                })

            if aspects_data:
                st.dataframe(pd.DataFrame(aspects_data), use_container_width=True, hide_index=True)
            else:
                st.info("Нет данных об аспектах.")

        # ------------------------------------------------
        # Вкладка: Прогрессии
        # ------------------------------------------------
        with tab_progressions:
            st.markdown("Вторичные прогрессии: 1 день после рождения = 1 год жизни.")

            pc1, pc2 = st.columns(2)
            with pc1:
                progression_date = st.date_input(
                    "Дата прогрессии", value=date.today(),
                    min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key="progression_date",
                )
            with pc2:
                progression_type_display = st.radio(
                    "Тип прогрессий", ["Вторичные (день за год)", "Солнечная дуга"], index=0, key="progression_type",
                )

            calculate_progressions_button = st.button("Рассчитать прогрессии", type="primary", key="calculate_progressions_button")

            if calculate_progressions_button:
                try:
                    birth = st.session_state["birth"]
                    settings = st.session_state["settings"]
                    progression_type = "secondary" if "Вторичные" in progression_type_display else "solar_arc"

                    if progression_type == "secondary":
                        progression_result = calculate_secondary_progressions(birth, progression_date.strftime("%Y-%m-%d"), settings)
                    else:
                        progression_result = calculate_solar_arc_progressions(birth, progression_date.strftime("%Y-%m-%d"), settings)

                    st.session_state["progression_result"] = progression_result
                    st.session_state["progression_type_used"] = progression_type
                except Exception as e:
                    st.error(f"Ошибка расчёта прогрессий: {e}")

            if "progression_result" in st.session_state:
                progression_result = st.session_state["progression_result"]
                progression_type_used = st.session_state.get("progression_type_used", "secondary")

                st.divider()

                i1, i2, i3 = st.columns(3)
                with i1:
                    st.metric("Дата прогрессии", progression_result["progression_date"])
                with i2:
                    st.metric("Возраст", f"{progression_result['age_years']} лет")
                with i3:
                    if progression_type_used == "solar_arc":
                        st.metric("Солнечная дуга", f"{progression_result.get('solar_arc', 0):.2f}°")
                    else:
                        st.metric("Тип", "Вторичные прогрессии")

                if progression_result.get("warnings"):
                    with st.expander("Предупреждения", expanded=False):
                        for warning in progression_result["warnings"]:
                            st.warning(warning)

                st.markdown("#### Прогрессивные планеты")
                planets_data = []
                for p in progression_result.get("planets", []):
                    planets_data.append({
                        "Планета": get_planet_name_ru(p["name"]),
                        "Знак": get_sign_name_ru(p["sign"]),
                        "Градус в знаке": round(p["degree_in_sign"], 2),
                        "Долгота": round(p["longitude"], 2),
                    })

                if planets_data:
                    st.dataframe(pd.DataFrame(planets_data), use_container_width=True, hide_index=True)
                else:
                    st.info("Нет данных о прогрессивных планетах.")

                if progression_result.get("additional_points"):
                    st.markdown("#### Прогрессивные точки (ASC, MC, Part of Fortune)")
                    points_data = []
                    for p in progression_result["additional_points"]:
                        points_data.append({
                            "Точка": get_planet_name_ru(p["name"]),
                            "Знак": get_sign_name_ru(p["sign"]),
                            "Градус в знаке": round(p["degree_in_sign"], 2),
                            "Долгота": round(p["longitude"], 2),
                        })

                    if points_data:
                        st.dataframe(pd.DataFrame(points_data), use_container_width=True, hide_index=True)

                st.markdown("#### Аспекты прогрессий к натальным точкам")
                try:
                    settings = st.session_state["settings"]
                    natal_result = st.session_state["chart_result"]
                    progression_aspects = find_progression_aspects(
                        natal_result["objects"], progression_result["objects"], settings,
                    )

                    if progression_aspects:
                        aspects_data = []
                        for a in progression_aspects:
                            aspects_data.append({
                                "Прогрессивная планета": get_planet_name_ru(a["progressed_planet"]),
                                "Аспект": get_aspect_name_ru(a["aspect"]),
                                "Натальная точка": get_planet_name_ru(a["natal_point"]),
                                "Орб": round(a["orb"], 2),
                                "Сила": round(a["strength"], 2),
                            })
                        st.dataframe(pd.DataFrame(aspects_data), use_container_width=True, hide_index=True)
                    else:
                        st.info("Аспекты прогрессий к натальным точкам не найдены.")
                except Exception as e:
                    st.warning(f"Не удалось рассчитать аспекты прогрессий: {e}")

                json_str = json.dumps(progression_result, ensure_ascii=False, indent=2)
                st.download_button(
                    "📥 Скачать прогрессии (JSON)", data=json_str,
                    file_name=f"progressions_{progression_result['progression_date']}.json", mime="application/json",
                )
            else:
                st.info("Выберите дату и тип прогрессий, затем нажмите «Рассчитать прогрессии».")

        # ------------------------------------------------
        # Вкладка: JSON
        # ------------------------------------------------
        with tab_json:
            st.json(result)

        # ------------------------------------------------
        # Таблица транзитов (результат расчёта)
        # ------------------------------------------------
        if "transit_result" in st.session_state:
            st.divider()
            st.subheader("Транзиты")

            transit_mode_used = st.session_state.get("transit_mode_used", "calendar")
            transit_period = st.session_state.get("transit_period", ("", ""))
            transit_result = st.session_state["transit_result"]

            st.markdown(f"**Период:** {transit_period[0]} — {transit_period[1]}")

            if transit_mode_used == "periods":
                st.markdown("**Режим:** Периоды активности (вход в орб → пик → выход из орба)")

                if transit_result:
                    periods_data = []
                    for period in transit_result:
                        start_dt = period.get("start_datetime", "")
                        exact_dt = period.get("exact_datetime", "")
                        end_dt = period.get("end_datetime", "")

                        start_date_part, start_time_part = start_dt.split("T") if "T" in start_dt else (start_dt, "")
                        exact_date_part, exact_time_part = exact_dt.split("T") if "T" in exact_dt else (exact_dt, "")
                        end_date_part, end_time_part = end_dt.split("T") if "T" in end_dt else (end_dt, "")

                        periods_data.append({
                            "Транзитная планета": get_planet_name_ru(period.get("transit_planet", "")),
                            "Аспект": get_aspect_name_ru(period.get("aspect", "")),
                            "Натальная точка": get_planet_name_ru(period.get("natal_point", "")),
                            "Направление": get_direction_name_ru(period.get("direction", "direct")),
                            "Вход в орб": f"{start_date_part} {start_time_part}",
                            "Пик (точный)": f"{exact_date_part} {exact_time_part}",
                            "Выход из орба": f"{end_date_part} {end_time_part}",
                            "Орб": period.get("orb", 0),
                        })

                    st.dataframe(pd.DataFrame(periods_data), use_container_width=True, hide_index=True)

                    json_str = json.dumps(transit_result, ensure_ascii=False, indent=2)
                    st.download_button("Скачать периоды активности (JSON)", data=json_str, file_name="transit_periods.json", mime="application/json")
                else:
                    st.info("Периоды активности не найдены.")

            elif transit_mode_used == "precise":
                st.markdown("**Режим:** Точный (с временем аспектов)")

                if transit_result:
                    events_data = []
                    for event in transit_result:
                        dt_str = event.get("exact_datetime", "")
                        date_part, time_part = dt_str.split("T") if "T" in dt_str else (dt_str, "")

                        events_data.append({
                            "Дата": date_part,
                            "Время": time_part,
                            "Направление": get_direction_name_ru(event.get("direction", "direct")),
                            "Транзитная планета": get_planet_name_ru(event.get("transit_planet", "")),
                            "Аспект": get_aspect_name_ru(event.get("aspect", "")),
                            "Натальная точка": get_planet_name_ru(event.get("natal_point", "")),
                        })

                    st.dataframe(pd.DataFrame(events_data), use_container_width=True, hide_index=True)

                    json_str = json.dumps(transit_result, ensure_ascii=False, indent=2)
                    st.download_button("Скачать транзиты (JSON)", data=json_str, file_name="precise_transits.json", mime="application/json")
                else:
                    st.info("Транзиты не найдены.")

            else:
                st.markdown("**Режим:** Быстрый (по дням)")

                if transit_result:
                    calendar_data = []
                    for entry in transit_result:
                        calendar_data.append({
                            "Дата": entry.get("date", ""),
                            "Транзитная планета": get_planet_name_ru(entry.get("transit_planet", "")),
                            "Аспект": get_aspect_name_ru(entry.get("aspect", "")),
                            "Натальная точка": get_planet_name_ru(entry.get("natal_point", "")),
                            "Орб": round(entry.get("orb", 0), 2),
                            "Сила": round(entry.get("strength", 0), 2),
                        })

                    st.dataframe(pd.DataFrame(calendar_data), use_container_width=True, hide_index=True)

                    json_str = json.dumps(transit_result, ensure_ascii=False, indent=2)
                    st.download_button("Скачать транзиты (JSON)", data=json_str, file_name="transit_calendar.json", mime="application/json")
                else:
                    st.info("Транзиты не найдены.")             