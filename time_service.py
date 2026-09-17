from datetime import datetime, timedelta


def parse_local_datetime(date_str, time_str, utc_offset_hours):
    """
    Преобразует локальные дату и время в UTC.

    Параметры:
        date_str: дата в формате YYYY-MM-DD
        time_str: время в формате HH:MM или HH:MM:SS
        utc_offset_hours: смещение от UTC в часах

    Возвращает:
        local_datetime, utc_datetime
    """

    if len(time_str) == 5:
        time_str = time_str + ":00"

    local_dt = datetime.fromisoformat(f"{date_str}T{time_str}")
    utc_dt = local_dt - timedelta(hours=float(utc_offset_hours))

    return local_dt, utc_dt


def datetime_to_jd(dt):
    """
    Преобразует datetime в Julian Day.

    Важно:
        Ожидается, что dt уже является UTC.
    """

    year = dt.year
    month = dt.month

    day_fraction = (
        dt.day
        + dt.hour / 24.0
        + dt.minute / 1440.0
        + dt.second / 86400.0
        + dt.microsecond / 86400000000.0
    )

    if month <= 2:
        year -= 1
        month += 12

    A = year // 100
    B = 2 - A + A // 4

    jd = (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + day_fraction
        + B
        - 1524.5
    )

    return float(jd)

def jd_to_datetime(jd):
    """
    Преобразует Julian Day в datetime UTC.

    Это обратная функция к datetime_to_jd.
    Используется для преобразования точных дат транзитов
    из Julian Day в читаемый формат.

    Параметры:
        jd: Julian Day

    Возвращает:
        datetime UTC
    """

    jd = jd + 0.5
    z = int(jd)
    f = jd - z

    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4

    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)

    day = b - d - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715

    hours = f * 24.0
    hour = int(hours)
    minutes = (hours - hour) * 60.0
    minute = int(minutes)
    seconds = (minutes - minute) * 60.0
    second = int(seconds)

    return datetime(year, month, day, hour, minute, second)