"""Итерация 39: Лилит/Селена/Прозерпина — расчёт, карта, профили."""
from astro_core.chart import build_natal_chart
from astro_core.display_profiles import apply_profile_to_settings, get_builtin_profile
from astro_core.ephemeris import calculate_hypothetical_point, initialize_ephemeris

BIRTH = {
    "name": "Тест",
    "date": "1971-03-17",
    "time": "11:30",
    "latitude": 55.7887,
    "longitude": 49.1221,
    "utc_offset_hours": 3.0,
}
JD = 2441028.0


def test_black_moon_always_available():
    initialize_ephemeris({})
    obj = calculate_hypothetical_point(JD, "BlackMoon", {})
    assert obj is not None
    assert 0.0 <= obj["longitude"] < 360.0
    assert obj["sign"]


def test_selena_proserpina_graceful_without_seorbel():
    initialize_ephemeris({})
    for name in ("Selena", "Proserpina"):
        obj = calculate_hypothetical_point(JD, name, {})
        assert obj is None or 0.0 <= obj["longitude"] < 360.0


def test_chart_contains_black_moon_and_gates():
    chart = build_natal_chart(BIRTH, {})
    names = [p["name"] for p in chart["additional_points"]]
    assert "BlackMoon" in names
    chart_off = build_natal_chart(
        BIRTH, {"include_black_moon": False,
                "include_selena": False,
                "include_proserpina": False})
    names_off = [p["name"] for p in chart_off["additional_points"]]
    assert "BlackMoon" not in names_off


def test_profiles_gate_new_points():
    full = apply_profile_to_settings(get_builtin_profile("full"))
    classic = apply_profile_to_settings(get_builtin_profile("classic"))
    minimal = apply_profile_to_settings(get_builtin_profile("minimal"))
    for key in ("include_black_moon", "include_selena", "include_proserpina"):
        assert full[key] is True
        assert classic[key] is False
        assert minimal[key] is False
