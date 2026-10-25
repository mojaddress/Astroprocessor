"""Итерация 34: Крест судьбы — формула и присутствие на карте."""
from astro_core.chart import build_natal_chart
from astro_core.points import cross_of_fate

BIRTH = {
    "name": "Тест",
    "date": "1971-03-17",
    "time": "11:30",
    "latitude": 55.7887,
    "longitude": 49.1221,
    "utc_offset_hours": 3.0,
}


def test_midpoint_formula():
    assert abs(cross_of_fate(10.0, 50.0) - 30.0) < 1e-9
    assert abs(cross_of_fate(350.0, 30.0) - 10.0) < 1e-9
    # Вырожденный случай (оппозиция): равноправны две середины дуги
    assert cross_of_fate(90.0, 270.0) in (0.0, 180.0)


def test_chart_contains_cross():
    chart = build_natal_chart(BIRTH, {})
    cross = [p for p in chart["additional_points"] if p["name"] == "CrossOfFate"]
    assert len(cross) == 1
    assert cross[0]["sign"]
    assert cross[0]["house"]


def test_chart_cross_disabled_by_setting():
    chart = build_natal_chart(BIRTH, {"include_cross_of_fate": False})
    names = [p["name"] for p in chart["additional_points"]]
    assert "CrossOfFate" not in names
