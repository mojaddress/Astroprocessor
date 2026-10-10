"""Итерация 19: DSC и Колесо Фортуны присутствуют в данных карты и отключаются настройками."""
from astro_core.chart import build_natal_chart

BIRTH = {
    "name": "Тест",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3.0,
}


def _names(points):
    return [p["name"] for p in points]


def test_dsc_present_by_default():
    chart = build_natal_chart(BIRTH, {})
    names = _names(chart["additional_points"])
    assert "ASC" in names and "MC" in names and "DSC" in names


def test_dsc_opposite_asc():
    chart = build_natal_chart(BIRTH, {})
    pts = {p["name"]: p["longitude"] for p in chart["additional_points"]}
    assert abs(((pts["ASC"] + 180.0) % 360.0) - pts["DSC"]) < 1e-6


def test_dsc_can_be_disabled():
    chart = build_natal_chart(BIRTH, {"include_dsc": False})
    assert "DSC" not in _names(chart["additional_points"])


def test_part_of_fortune_present():
    chart = build_natal_chart(BIRTH, {})
    assert "PartOfFortune" in _names(chart["additional_points"])