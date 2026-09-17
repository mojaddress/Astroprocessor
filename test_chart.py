import pytest

from astro_core.chart import build_natal_chart
from astro_core.ephemeris import SWISSEPH_AVAILABLE


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_build_demo_chart():
    birth = {
        "name": "Demo Person",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
        "timezone": "Europe/Moscow",
    }

    settings = {
        "include_chiron": False,
        "include_nodes": False,
    }

    result = build_natal_chart(birth, settings)

    assert result["meta"]["stage"] == "0.8.0"

    assert len(result["planets"]) == 10

    assert result["planets"][0]["name"] == "Sun"
    assert result["planets"][0]["sign"] == "Taurus"

    assert len(result["houses"]) == 12

    assert isinstance(result["aspects"], list)

    assert "warnings" in result