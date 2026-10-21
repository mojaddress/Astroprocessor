"""Итерация 27: дирекции солнечной дуги (правильная логика)."""
from datetime import date

from astro_core.chart import build_natal_chart
from astro_core.directions import (
    calculate_directions, directed_planets, solar_arc,
    _years_between,
)

BIRTH = {
    "name": "Тест",
    "date": "1990-05-15",
    "time": "12:00",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3.0,
}


def test_years_between_basic():
    assert _years_between(date(1990, 5, 15), date(1990, 5, 15)) == 0
    assert _years_between(date(1990, 5, 15), date(1991, 5, 15)) == 1
    assert _years_between(date(1990, 5, 15), date(1991, 5, 14)) == 0
    assert _years_between(date(1990, 5, 15), date(2020, 5, 15)) == 30


def test_solar_arc_zero_at_birth():
    natal = build_natal_chart(BIRTH, {})
    assert solar_arc(natal, date(1990, 5, 15)) < 0.2  # реалистичная погрешность эфемерид


def test_arc_about_one_degree_per_year():
    natal = build_natal_chart(BIRTH, {})
    arc = solar_arc(natal, date(1991, 5, 15))
    assert 0.9 < arc < 1.1


def test_arc_about_thirty_degrees_in_30_years():
    natal = build_natal_chart(BIRTH, {})
    arc = solar_arc(natal, date(2020, 5, 15))
    assert 28.0 < arc < 32.0  # Солнце движется неравномерно (~0.96°/день в мае)


def test_directed_planets_shifted_by_arc():
    natal = build_natal_chart(BIRTH, {})
    result = calculate_directions(natal, date(2020, 5, 15))
    arc = result["arc"]
    for p, np_ in zip(result["planets"], natal["planets"]):
        assert abs(((p["longitude"] - np_["longitude"]) % 360.0) - arc) < 1e-6


def test_aspects_cross_only_with_expected_keys():
    natal = build_natal_chart(BIRTH, {})
    result = calculate_directions(natal, date(2020, 5, 15))
    for a in result["aspects"]:
        assert {"dir_planet", "natal_point", "aspect", "orb", "score"} <= set(a)
