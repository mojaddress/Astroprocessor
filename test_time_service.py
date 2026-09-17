from datetime import datetime

from astro_core.time_service import parse_local_datetime, datetime_to_jd


def test_parse_local_datetime_positive_offset():
    local_dt, utc_dt = parse_local_datetime("1990-05-15", "14:30", 3)

    assert local_dt == datetime(1990, 5, 15, 14, 30, 0)
    assert utc_dt == datetime(1990, 5, 15, 11, 30, 0)


def test_parse_local_datetime_negative_offset():
    local_dt, utc_dt = parse_local_datetime("2000-01-01", "00:30", -5)

    assert local_dt == datetime(2000, 1, 1, 0, 30, 0)
    assert utc_dt == datetime(2000, 1, 1, 5, 30, 0)


def test_parse_local_datetime_zero_offset():
    local_dt, utc_dt = parse_local_datetime("2000-01-01", "12:00", 0)

    assert local_dt == datetime(2000, 1, 1, 12, 0, 0)
    assert utc_dt == datetime(2000, 1, 1, 12, 0, 0)


def test_datetime_to_jd_j2000():
    dt = datetime(2000, 1, 1, 12, 0, 0)
    jd = datetime_to_jd(dt)

    assert abs(jd - 2451545.0) < 1e-6