"""
Тесты для поддержки сидерического зодиака.

Проверяют:
- расчёт натальной карты в сидерическом зодиаке;
- отличие позиций планет от тропического зодиака;
- корректность мета-данных.
"""

import pytest

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
def test_tropical_chart(birth_data):
    """Проверка расчёта карты в тропическом зодиаке."""
    settings = {
        "zodiac": "tropical",
        "include_chiron": False,
        "include_nodes": False,
    }
    result = build_natal_chart(birth_data, settings)

    assert result["meta"]["zodiac"] == "tropical"
    assert result["meta"]["ayanamsha"] is None
    assert len(result["planets"]) > 0


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_sidereal_chart(birth_data):
    """Проверка расчёта карты в сидерическом зодиаке."""
    settings = {
        "zodiac": "sidereal",
        "ayanamsha": "lahiri",
        "include_chiron": False,
        "include_nodes": False,
    }
    result = build_natal_chart(birth_data, settings)

    assert result["meta"]["zodiac"] == "sidereal"
    assert result["meta"]["ayanamsha"] == "lahiri"
    assert len(result["planets"]) > 0


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_sidereal_positions_differ_from_tropical(birth_data):
    """Проверка, что позиции планет в сидерическом зодиаке отличаются от тропического."""
    tropical_settings = {
        "zodiac": "tropical",
        "include_chiron": False,
        "include_nodes": False,
    }
    tropical_result = build_natal_chart(birth_data, tropical_settings)

    sidereal_settings = {
        "zodiac": "sidereal",
        "ayanamsha": "lahiri",
        "include_chiron": False,
        "include_nodes": False,
    }
    sidereal_result = build_natal_chart(birth_data, sidereal_settings)

    # Находим Солнце в обоих результатах
    tropical_sun = next((p for p in tropical_result["planets"] if p["name"] == "Sun"), None)
    sidereal_sun = next((p for p in sidereal_result["planets"] if p["name"] == "Sun"), None)

    assert tropical_sun is not None
    assert sidereal_sun is not None

    # Долготы должны отличаться (примерно на 24° для Лахири)
    longitude_diff = abs(tropical_sun["longitude"] - sidereal_sun["longitude"])
    assert longitude_diff > 20.0  # Разница должна быть значительной
    assert longitude_diff < 30.0  # Но не больше 30°


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_different_ayanamsha(birth_data):
    """Проверка, что разные системы ayanamsha дают разные результаты."""
    lahiri_settings = {
        "zodiac": "sidereal",
        "ayanamsha": "lahiri",
        "include_chiron": False,
        "include_nodes": False,
    }
    lahiri_result = build_natal_chart(birth_data, lahiri_settings)

    fagan_settings = {
        "zodiac": "sidereal",
        "ayanamsha": "fagan_brady",
        "include_chiron": False,
        "include_nodes": False,
    }
    fagan_result = build_natal_chart(birth_data, fagan_settings)

    # Находим Солнце в обоих результатах
    lahiri_sun = next((p for p in lahiri_result["planets"] if p["name"] == "Sun"), None)
    fagan_sun = next((p for p in fagan_result["planets"] if p["name"] == "Sun"), None)

    assert lahiri_sun is not None
    assert fagan_sun is not None

    # Долготы должны немного отличаться (разные ayanamsha)
    assert lahiri_sun["longitude"] != fagan_sun["longitude"]