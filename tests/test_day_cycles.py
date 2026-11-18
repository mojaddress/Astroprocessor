"""Суточные циклы: чистые функции, инварианты восхода, планетарные часы."""
import math
from datetime import datetime

import pytest

from astro_core import day_cycles as dc

MOSCOW = (55.7558, 37.6173, 3.0)


def test_lunar_day_from_elongation():
    assert dc._lunar_day_from_elongation(0.0) == 1
    assert dc._lunar_day_from_elongation(11.9) == 1
    assert dc._lunar_day_from_elongation(12.0) == 2
    assert dc._lunar_day_from_elongation(359.9) == 30


def test_phase_from_elongation():
    assert dc._phase_from_elongation(0.0) == "Новолуние"
    assert dc._phase_from_elongation(90.0) == "Первая четверть"
    assert dc._phase_from_elongation(180.0) == "Полнолуние"
    assert dc._phase_from_elongation(270.0) == "Последняя четверть"


def test_chaldean_rotation_from_sun():
    assert dc._chaldean_from("Sun")[:7] == [
        "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]


def test_day_rulers_weekday():
    assert dc.DAY_RULERS[datetime(2026, 11, 16).weekday()] == "Moon"  # понедельник
    assert dc.DAY_RULERS[datetime(2026, 11, 21).weekday()] == "Saturn"  # суббота


def test_sun_altitude_range():
    jd = dc._jd_from_local(datetime(2026, 6, 21, 12, 0), 3.0)
    alt = dc.sun_altitude(jd, *MOSCOW[:2])
    assert 50.0 < alt < 62.0, f"полуденная высота летом вне разумного: {alt}"


def test_sun_events_order_and_day_length():
    events = dc.sun_events(datetime(2026, 3, 20), *MOSCOW)
    assert not events["polar"]
    assert events["rise"] < events["set"]
    day_hours = (events["set"] - events["rise"]) * 24
    assert 11.0 < day_hours < 13.5, f"долгота дня в равноденствие: {day_hours}"


def test_summer_day_longer_than_winter():
    summer = dc.sun_events(datetime(2026, 6, 21), *MOSCOW)
    winter = dc.sun_events(datetime(2026, 12, 21), *MOSCOW)
    assert (summer["set"] - summer["rise"]) > (winter["set"] - winter["rise"])


def test_polar_day_detected():
    events = dc.sun_events(datetime(2026, 6, 21), 78.0, 15.0, 1.0)
    assert events["polar"] and events["polar_day"]
    assert dc.planetary_hours(datetime(2026, 6, 21), 78.0, 15.0, 1.0) == []


def test_planetary_hours_structure():
    midnight = datetime(2026, 3, 20)
    hours = dc.planetary_hours(midnight, *MOSCOW)
    assert len(hours) == 24
    assert hours[0]["ruler"] == dc.DAY_RULERS[midnight.weekday()]
    day_lengths = {(h["end_jd"] - h["start_jd"]) for h in hours if h["kind"] == "day"}
    night_lengths = {(h["end_jd"] - h["start_jd"]) for h in hours if h["kind"] == "night"}
    assert len(day_lengths) == 1 and len(night_lengths) == 1
    sequence = [h["ruler"] for h in hours]
    assert sequence == dc._chaldean_from(sequence[0])
    assert hours[0]["start_jd"] < hours[-1]["end_jd"]


def test_lunar_day_in_range():
    jd = dc._jd_from_local(datetime(2026, 11, 16, 12, 0), 3.0)
    assert 1 <= dc.lunar_day(jd) <= 30
    assert dc.moon_phase(jd) in dc.PHASE_NAMES
