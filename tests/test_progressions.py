"""
Тесты для модуля прогрессий.

Проверяют:
- расчёт вторичных прогрессий;
- расчёт прогрессий солнечной дуги;
- аспекты между прогрессивными и натальными точками.
"""

import pytest

from astro_core.progressions import (
    calculate_secondary_progressions,
    calculate_solar_arc_progressions,
    find_progression_aspects,
)
from astro_core.chart import build_natal_chart
from astro_core.ephemeris import SWISSEPH_AVAILABLE


@pytest.fixture
def birth_data():
    """Фикстура: данные рождения для тестов."""
    return {
        "name": "Test",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_secondary_progressions_basic(birth_data):
    """Проверка базового расчёта вторичных прогрессий."""
    progression_date = "2020-05-15"  # 30 лет

    result = calculate_secondary_progressions(birth_data, progression_date)

    assert result["progression_type"] == "secondary"
    assert result["progression_date"] == progression_date
    assert result["age_years"] > 29.0
    assert result["age_years"] < 31.0
    assert len(result["planets"]) > 0
    assert len(result["objects"]) > 0


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_secondary_progressions_age_zero(birth_data):
    """Проверка, что прогрессии на дату рождения равны натальной карте."""
    progression_date = birth_data["date"]

    result = calculate_secondary_progressions(birth_data, progression_date)

    assert result["age_days"] == 0
    assert result["age_years"] == 0.0

    # Прогрессивная карта на дату рождения должна быть равна натальной
    natal = build_natal_chart(birth_data, {"include_chiron": False, "include_nodes": False})

    # Сравниваем долготу Солнца
    natal_sun = next((p for p in natal["planets"] if p["name"] == "Sun"), None)
    progressed_sun = next((p for p in result["planets"] if p["name"] == "Sun"), None)

    assert natal_sun is not None
    assert progressed_sun is not None
    assert abs(natal_sun["longitude"] - progressed_sun["longitude"]) < 0.1


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_secondary_progressions_sun_moves(birth_data):
    """Проверка, что прогрессивное Солнце движется примерно на 1° в год."""
    # Прогрессии на 10 лет
    progression_date_10 = "2000-05-15"
    result_10 = calculate_secondary_progressions(birth_data, progression_date_10)

    # Прогрессии на 20 лет
    progression_date_20 = "2010-05-15"
    result_20 = calculate_secondary_progressions(birth_data, progression_date_20)

    sun_10 = next((p for p in result_10["planets"] if p["name"] == "Sun"), None)
    sun_20 = next((p for p in result_20["planets"] if p["name"] == "Sun"), None)

    assert sun_10 is not None
    assert sun_20 is not None

    # Разница в долготе Солнца должна быть примерно 10° (1° в год × 10 лет)
    lon_diff = abs(sun_20["longitude"] - sun_10["longitude"])
    assert 8.0 < lon_diff < 12.0


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_solar_arc_progressions_basic(birth_data):
    """Проверка базового расчёта прогрессий солнечной дуги."""
    progression_date = "2020-05-15"  # 30 лет

    result = calculate_solar_arc_progressions(birth_data, progression_date)

    assert result["progression_type"] == "solar_arc"
    assert result["progression_date"] == progression_date
    assert "solar_arc" in result
    assert len(result["planets"]) > 0
    assert len(result["objects"]) > 0


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_solar_arc_progressions_arc_value(birth_data):
    """Проверка, что солнечная дуга положительна и разумна."""
    progression_date = "2020-05-15"  # 30 лет

    result = calculate_solar_arc_progressions(birth_data, progression_date)

    solar_arc = result["solar_arc"]

    # Солнечная дуга должна быть положительной и меньше 360°
    assert 0.0 < solar_arc < 360.0

    # Для 30 лет дуга должна быть примерно 30° (1° в год)
    assert 25.0 < solar_arc < 35.0


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_solar_arc_all_planets_move_same_amount(birth_data):
    """Проверка, что все планеты продвигаются на одинаковую величину."""
    progression_date = "2020-05-15"  # 30 лет

    settings = {"include_chiron": False, "include_nodes": False}
    natal = build_natal_chart(birth_data, settings)
    result = calculate_solar_arc_progressions(birth_data, progression_date, settings)

    solar_arc = result["solar_arc"]

    # Проверяем, что каждая планета продвинулась на солнечную дугу
    for progressed_obj in result["planets"]:
        planet_name = progressed_obj["name"]
        natal_obj = next((p for p in natal["planets"] if p["name"] == planet_name), None)

        if natal_obj is None:
            continue

        from astro_core.utils import normalize_longitude
        expected_lon = normalize_longitude(natal_obj["longitude"] + solar_arc)

        assert abs(progressed_obj["longitude"] - expected_lon) < 0.01


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_progression_aspects(birth_data):
    """Проверка расчёта аспектов между прогрессивными и натальными точками."""
    progression_date = "2020-05-15"  # 30 лет

    settings = {"include_chiron": False, "include_nodes": False}
    natal = build_natal_chart(birth_data, settings)
    progressed = calculate_secondary_progressions(birth_data, progression_date, settings)

    aspects = find_progression_aspects(natal["objects"], progressed["objects"], settings)

    # Должны быть какие-то аспекты
    assert len(aspects) > 0

    # Проверяем структуру аспектов
    for aspect in aspects:
        assert "progressed_planet" in aspect
        assert "natal_point" in aspect
        assert "aspect" in aspect
        assert "orb" in aspect
        assert "strength" in aspect