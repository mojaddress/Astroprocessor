"""
Модуль для работы с часовыми поясами и определения точного смещения от Гринвича.

Использует базу данных часовых поясов (формат IANA) для точного определения
смещения от Гринвича с учётом летнего времени.

Это критично для астрологических расчётов: ошибка в 1 час может изменить
положение Луны, куспиды домов и положение Асцендента.

Важно:
    Для работы требуется пакет `tzdata` (устанавливается через `pip install tzdata`).
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_utc_offset_hours(timezone_name, dt):
    """
    Возвращает точное смещение от Гринвича в часах для указанного часового пояса и даты.

    Учитывает летнее время: если на указанную дату действует летнее время,
    возвращается соответствующее смещение.

    Параметры:
        timezone_name: название часового пояса в формате IANA (например, "Europe/Moscow")
        dt: объект datetime, для которого определяется смещение

    Возвращает:
        смещение от Гринвича в часах (например, 3.0, 4.0, -5.0)

    Исключения:
        ValueError: если часовой пояс не найден
    """
    try:
        tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise ValueError(f"Неизвестный часовой пояс: {timezone_name}")

    # Привязываем часовой пояс к дате
    localized_dt = dt.replace(tzinfo=tz)

    # Получаем смещение от Гринвича
    utc_offset = localized_dt.utcoffset()

    if utc_offset is None:
        raise ValueError(f"Не удалось определить смещение от Гринвича для: {timezone_name}")

    # Переводим в часы (может быть дробным для некоторых поясов)
    total_seconds = utc_offset.total_seconds()
    hours = total_seconds / 3600

    return hours


def get_timezone_info(timezone_name, dt):
    """
    Возвращает подробную информацию о часовом поясе для указанной даты.

    Параметры:
        timezone_name: название часового пояса в формате IANA
        dt: объект datetime

    Возвращает:
        словарь с информацией:
        - timezone: название часового пояса
        - utc_offset: смещение от Гринвича в часах
        - utc_offset_str: смещение в формате "+03:00"
        - is_dst: действует ли летнее время
        - tz_name: короткое название часового пояса (например, "МСК")
    """
    try:
        tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise ValueError(f"Неизвестный часовой пояс: {timezone_name}")

    localized_dt = dt.replace(tzinfo=tz)

    utc_offset = localized_dt.utcoffset()
    if utc_offset is None:
        raise ValueError(f"Не удалось определить смещение от Гринвича для: {timezone_name}")

    # Определяем, действует ли летнее время
    dst_offset = localized_dt.dst()
    is_dst = dst_offset is not None and dst_offset.total_seconds() > 0

    # Форматируем смещение
    total_seconds = utc_offset.total_seconds()
    hours = total_seconds / 3600

    # Формат "+03:00" или "-05:00"
    sign = "+" if hours >= 0 else "-"
    abs_hours = int(abs(hours))
    minutes = int(abs(abs(hours) - abs_hours) * 60)
    utc_offset_str = f"{sign}{abs_hours:02d}:{minutes:02d}"

    return {
        "timezone": timezone_name,
        "utc_offset": hours,
        "utc_offset_str": utc_offset_str,
        "is_dst": is_dst,
    }


def parse_birth_datetime(date_str, time_str, timezone_name):
    """
    Создаёт объект datetime из строки даты, строки времени и названия часового пояса.

    Параметры:
        date_str: дата в формате "ГГГГ-ММ-ДД"
        time_str: время в формате "ЧЧ:ММ"
        timezone_name: название часового пояса в формате IANA

    Возвращает:
        объект datetime с привязанным часовым поясом
    """
    if len(time_str) == 5:
        time_str = time_str + ":00"

    dt = datetime.fromisoformat(f"{date_str}T{time_str}")

    try:
        tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise ValueError(f"Неизвестный часовой пояс: {timezone_name}")

    return dt.replace(tzinfo=tz)