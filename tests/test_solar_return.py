"""Итерация 30: солнечные обращения."""
from datetime import date

from astro_core.chart import build_natal_chart
from astro_core.constants import DEFAULT_SETTINGS
from astro_core.ephemeris import calculate_objects, initialize_ephemeris
from astro_core.solar_return import (
    calculate_solar_return, solar_return_moment,
)
from astro_core.time_service import datetime_to_jd

BIRTH = {
    "name": "Тест",
    "date": "1971-03-17",
    "time": "11:30",
    "latitude": 55.7887,
    "longitude": 49.1221,
    "utc_offset_hours": 3.0,
}


def test_moment_near_birthday():
    natal = build_natal_chart(BIRTH, {})
    m = solar_return_moment(natal, 2026)
    assert date(2026, 3, 15) <= m.date() <= date(2026, 3, 19)


def test_sun_returns_to_natal_longitude():
    natal = build_natal_chart(BIRTH, {})
    m = solar_return_moment(natal, 2026)
    initialize_ephemeris(dict(DEFAULT_SETTINGS))
    objs, _ = calculate_objects(datetime_to_jd(m), dict(DEFAULT_SETTINGS))
    sun = next(o for o in objs if o["name"] == "Sun")
    natal_sun = next(p["longitude"] for p in natal["planets"] if p["name"] == "Sun")
    diff = abs((sun["longitude"] - natal_sun + 180) % 360 - 180)
    assert diff < 0.02


def test_chart_built():
    natal = build_natal_chart(BIRTH, {})
    sr = calculate_solar_return(natal, 2026, 55.7887, 49.1221)
    assert sr["chart"]["planets"]
    assert any(p["name"] == "ASC" for p in sr["chart"]["additional_points"])
    assert "соляр 2026" in sr["chart"]["birth"]["name"]
