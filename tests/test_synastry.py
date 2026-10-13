"""Итерация 21: синастрия и локальные интерпретации."""
from astro_core.chart import build_natal_chart
from astro_core.controllers.synastry_controller import SynastryController
from astro_core.interpretations import (
    ASPECT_INFO, aspect_tooltip, summarize_natal, summarize_synastry,
    summarize_transits,
)

BIRTH_A = {
    "name": "Анна", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173, "utc_offset_hours": 3.0,
}
BIRTH_B = {
    "name": "Сергей", "date": "1971-03-17", "time": "11:30",
    "latitude": 55.7887, "longitude": 49.1221, "utc_offset_hours": 3.0,
}


def _charts():
    return build_natal_chart(BIRTH_A, {}), build_natal_chart(BIRTH_B, {})


def test_synastry_cross_aspects_only():
    a, b = _charts()
    result = SynastryController().calculate_synastry(a, b)
    names_a = {p["name"] for p in a["planets"]}
    names_b = {p["name"] for p in b["planets"]}
    for asp in result.aspects:
        pa, pb = asp["point_a"], asp["point_b"]
        cross = (pa in names_a and pb in names_b) or (pa in names_b and pb in names_a)
        assert cross


def test_synastry_score_bounds():
    a, b = _charts()
    result = SynastryController().calculate_synastry(a, b)
    assert 0.0 <= result.compatibility_percentage <= 100.0
    assert isinstance(result.total_score, int)


def test_aspect_tooltip_for_all_aspects():
    for aspect in ASPECT_INFO:
        tip = aspect_tooltip(aspect, "Sun", "Moon")
        assert "Солнце" in tip and len(tip) > 20


def test_summarize_natal_contains_core():
    a, _ = _charts()
    text = summarize_natal(a)
    assert "Портрет: Анна" in text
    assert "Солнце" in text


def test_summarize_synastry_and_transits():
    a, b = _charts()
    result = SynastryController().calculate_synastry(a, b)
    text = summarize_synastry(result.aspects, "Анна", "Сергей")
    assert isinstance(text, str) and len(text) > 10
    events = [{"transit_planet": "Sun", "natal_point": "Venus", "aspect": "trine"}]
    tr = summarize_transits(a, events)
    assert "Поддерживающие периоды" in tr