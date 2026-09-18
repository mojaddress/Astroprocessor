from datetime import datetime, timedelta

from .constants import ASPECT_DEFINITIONS, DEFAULT_SETTINGS, DEFAULT_TRANSIT_PLANETS
from .ephemeris import calculate_objects, initialize_ephemeris, get_planet_position
from .time_service import parse_local_datetime, datetime_to_jd, jd_to_datetime
from .utils import angle_between


def calculate_transit_positions(julian_day, settings=None):
    """
    Рассчитывает положения транзитных планет на заданную дату.

    Параметры:
        julian_day: Julian Day даты транзита
        settings: настройки расчёта

    Настройки могут содержать:
        transit_planets: список имён транзитных планет
        include_chiron: включать ли Хирон (по умолчанию False для транзитов)
        include_nodes: включать ли лунные узлы (по умолчанию False для транзитов)
        zodiac: тип зодиака - "tropical" или "sidereal" (по умолчанию "tropical")
        ayanamsha: система ayanamsha для сидерического зодиака (по умолчанию "lahiri")
        ephe_path: путь к файлам эфемерид (опционально)

    Возвращает:
        transit_objects, warnings
    """

    if settings is None:
        settings = {}

    # Инициализируем путь к эфемеридам, если он указан.
    initialize_ephemeris(settings)

    transit_planets = settings.get("transit_planets", DEFAULT_TRANSIT_PLANETS)

    # Для транзитов по умолчанию не включаем Хирон и узлы,
    # но это можно изменить через настройки.
    # Создаём копию настроек, чтобы не изменять исходные.
    transit_settings = dict(settings)
    transit_settings["include_chiron"] = settings.get("include_chiron", False)
    transit_settings["include_nodes"] = settings.get("include_nodes", False)

    # calculate_objects возвращает два значения: (objects, warnings)
    objects, warnings = calculate_objects(julian_day, transit_settings)

    # Оставляем только те объекты, которые нужны как транзитные.
    transit_objects = [obj for obj in objects if obj["name"] in transit_planets]

    return transit_objects, warnings


def find_transits_on_date(natal_objects, transit_objects, settings=None):
    """
    Находит аспекты между транзитными планетами и натальными точками
    на конкретную дату.

    Параметры:
        natal_objects: список объектов натальной карты
        transit_objects: список объектов транзитной карты
        settings: настройки аспектов и орбов

    Возвращает:
        список транзитов
    """

    if settings is None:
        settings = DEFAULT_SETTINGS

    transits = []

    enabled_aspects = set(settings.get("enabled_aspects", DEFAULT_SETTINGS.get("enabled_aspects", [])))
    orbs = settings.get("orbs", DEFAULT_SETTINGS.get("orbs", {}))

    aspect_definitions = [
        a for a in ASPECT_DEFINITIONS
        if a["name"] in enabled_aspects
    ]

    if not aspect_definitions:
        return transits

    for transit_obj in transit_objects:
        if "longitude" not in transit_obj or "name" not in transit_obj:
            continue

        for natal_obj in natal_objects:
            if "longitude" not in natal_obj or "name" not in natal_obj:
                continue

            angle = angle_between(transit_obj["longitude"], natal_obj["longitude"])
            best_aspect = None

            for aspect_def in aspect_definitions:
                aspect_name = aspect_def["name"]
                exact_angle = float(aspect_def["angle"])
                max_orb = float(orbs.get(aspect_name, 0.0))

                if max_orb <= 0.0:
                    continue

                orb = abs(angle - exact_angle)

                if orb <= max_orb:
                    strength = 1.0 - (orb / max_orb)

                    candidate = {
                        "transit_planet": transit_obj["name"],
                        "natal_point": natal_obj["name"],
                        "aspect": aspect_name,
                        "angle": round(angle, 6),
                        "exact_angle": exact_angle,
                        "orb": round(orb, 6),
                        "max_orb": max_orb,
                        "strength": round(max(0.0, min(1.0, strength)), 6),
                        "transit_longitude": transit_obj["longitude"],
                        "natal_longitude": natal_obj["longitude"],
                    }

                    if best_aspect is None or candidate["orb"] < best_aspect["orb"]:
                        best_aspect = candidate

            if best_aspect is not None:
                transits.append(best_aspect)

    return transits


def get_transit_calendar(natal_objects, start_date, end_date, settings=None,
                         filter_planets=None, filter_aspects=None):
    """
    Возвращает календарь транзитов за период (по дням).

    Параметры:
        natal_objects: список объектов натальной карты
        start_date: начальная дата (ГГГГ-ММ-ДД)
        end_date: конечная дата (ГГГГ-ММ-ДД)
        settings: настройки расчёта
        filter_planets: список имён транзитных планет для фильтрации (None = все)
        filter_aspects: список имён аспектов для фильтрации (None = все)

    Возвращает:
        список транзитов с датами
    """

    if settings is None:
        settings = DEFAULT_SETTINGS

    calendar = []

    # Определяем список аспектов с учётом фильтрации
    enabled_aspects = set(settings.get("enabled_aspects", DEFAULT_SETTINGS.get("enabled_aspects", [])))
    if filter_aspects is not None and len(filter_aspects) > 0:
        enabled_aspects = enabled_aspects.intersection(set(filter_aspects))

    # Определяем список транзитных планет с учётом фильтрации
    transit_planets = settings.get("transit_planets", DEFAULT_TRANSIT_PLANETS)
    if filter_planets is not None and len(filter_planets) > 0:
        transit_planets = [p for p in transit_planets if p in filter_planets]

    # Создаём модифицированные настройки для find_transits_on_date
    filtered_settings = dict(settings)
    filtered_settings["enabled_aspects"] = list(enabled_aspects)
    filtered_settings["transit_planets"] = transit_planets

    # Парсим даты начала и конца
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    # Смещение UTC для дат транзитов
    utc_offset = settings.get("transit_utc_offset", 0)

    current_dt = start_dt

    while current_dt <= end_dt:
        date_str = current_dt.strftime("%Y-%m-%d")

        # Используем полдень как момент для расчёта транзитов на этот день
        local_dt, utc_dt = parse_local_datetime(date_str, "12:00", utc_offset)
        jd = datetime_to_jd(utc_dt)

        # Рассчитываем транзитные позиции на этот день с фильтрацией планет
        transit_objects, warnings = calculate_transit_positions(jd, filtered_settings)

        # Применяем фильтрацию планет к результатам
        if filter_planets is not None and len(filter_planets) > 0:
            transit_objects = [obj for obj in transit_objects if obj["name"] in filter_planets]

        # Находим транзиты к натальным точкам
        transits = find_transits_on_date(natal_objects, transit_objects, filtered_settings)

        # Добавляем дату к каждому транзиту
        for transit in transits:
            transit["date"] = date_str
            calendar.append(transit)

        # Переходим к следующему дню
        current_dt += timedelta(days=1)

    return calendar


def normalize_diff(diff):
    """
    Нормализует разницу углов к диапазону [-180, 180).
    Это нужно для корректного определения пересечения целевой долготы,
    в том числе при переходе через 0°/360°.
    """
    diff = diff % 360.0
    if diff >= 180.0:
        diff -= 360.0
    return diff


def get_aspect_target_longitudes(natal_longitude, aspect_angle):
    """
    Возвращает целевые долготы для аспекта.

    Для соединения (0°) и оппозиции (180°) целевая долгота одна.
    Для остальных аспектов (секстиль, квадрат, трин) целевых долготы две:
    natal_longitude + aspect_angle и natal_longitude - aspect_angle.

    Параметры:
        natal_longitude: долгота натальной точки
        aspect_angle: угол аспекта (0, 60, 90, 120, 180)

    Возвращает:
        список целевых долгот
    """
    from .utils import normalize_longitude

    targets = []

    if aspect_angle == 0:
        targets.append(normalize_longitude(natal_longitude))
    elif aspect_angle == 180:
        targets.append(normalize_longitude(natal_longitude + 180.0))
    else:
        targets.append(normalize_longitude(natal_longitude + aspect_angle))
        targets.append(normalize_longitude(natal_longitude - aspect_angle))

    return targets


def find_longitude_crossings(jd_start, jd_end, planet_name, target_longitude,
                             step_days=0.25, settings=None):
    """
    Находит моменты, когда планета пересекает целевую долготу.

    Параметры:
        jd_start: Julian Day начала периода
        jd_end: Julian Day конца периода
        planet_name: имя планеты
        target_longitude: целевая долгота
        step_days: шаг сканирования в днях (по умолчанию 0.25 = 6 часов)
        settings: настройки расчёта (для поддержки сидерического зодиака)

    Возвращает:
        список Julian Day моментов пересечения
    """
    crossings = []

    jd = jd_start
    prev_lon = None
    prev_jd = None

    while jd <= jd_end:
        lon, _ = get_planet_position(jd, planet_name, settings)

        if prev_lon is not None:
            diff_prev = normalize_diff(prev_lon - target_longitude)
            diff_curr = normalize_diff(lon - target_longitude)

            # Пересечение, если знак разницы изменился
            crossed = False

            if diff_prev == 0.0:
                crossed = True
            elif diff_curr == 0.0:
                crossed = True
            elif (diff_prev > 0 and diff_curr < 0) or (diff_prev < 0 and diff_curr > 0):
                # Проверяем, что это не скачок через 0/360
                if abs(diff_prev - diff_curr) < 180.0:
                    crossed = True

            if crossed:
                # Уточняем время пересечения через бинарный поиск
                refined_jd = refine_crossing(prev_jd, jd, planet_name, target_longitude,
                                             settings=settings)
                crossings.append(refined_jd)

        prev_lon = lon
        prev_jd = jd
        jd += step_days

    return crossings


def refine_crossing(jd_low, jd_high, planet_name, target_longitude,
                    max_iterations=50, settings=None):
    """
    Уточняет время пересечения целевой долготы через бинарный поиск.

    Параметры:
        jd_low: Julian Day нижней границы
        jd_high: Julian Day верхней границы
        planet_name: имя планеты
        target_longitude: целевая долгота
        max_iterations: максимальное число итераций
        settings: настройки расчёта (для поддержки сидерического зодиака)

    Возвращает:
        Julian Day момента пересечения
    """
    for _ in range(max_iterations):
        jd_mid = (jd_low + jd_high) / 2.0

        lon_mid, _ = get_planet_position(jd_mid, planet_name, settings)
        diff_mid = normalize_diff(lon_mid - target_longitude)

        if abs(diff_mid) < 1e-9:
            return jd_mid

        lon_low, _ = get_planet_position(jd_low, planet_name, settings)
        diff_low = normalize_diff(lon_low - target_longitude)

        if (diff_low > 0 and diff_mid > 0) or (diff_low < 0 and diff_mid < 0):
            jd_low = jd_mid
        else:
            jd_high = jd_mid

    return (jd_low + jd_high) / 2.0


def get_step_for_planet(planet_name):
    """
    Возвращает шаг сканирования в днях для планеты.

    Быстрые планеты (Луна) требуют меньшего шага, чтобы не пропустить
    пересечения. Медленные планеты (Сатурн и дальше) могут использовать
    больший шаг для ускорения расчётов.

    Параметры:
        planet_name: имя планеты

    Возвращает:
        шаг сканирования в днях
    """
    if planet_name == "Moon":
        return 0.05  # ~1 час
    elif planet_name in ("Sun", "Mercury", "Venus", "Mars"):
        return 0.25  # 6 часов
    else:
        return 1.0  # 1 день


def find_transit_events(natal_objects, start_date, end_date, settings=None,
                        filter_planets=None, filter_aspects=None):
    """
    Находит все события транзитов за период с точными датами.

    Для каждой пары (транзитная планета, натальная точка) и каждого аспекта
    функция находит моменты, когда транзитная планета делает точный аспект
    к натальной точке. Определяется направление движения (директное или
    ретроградное). Ретроградные петли учитываются автоматически: если
    планета проходит одну и ту же целевую долготу несколько раз, каждое
    пересечение становится отдельным событием.

    Параметры:
        natal_objects: список объектов натальной карты
        start_date: начальная дата (ГГГГ-ММ-ДД)
        end_date: конечная дата (ГГГГ-ММ-ДД)
        settings: настройки расчёта
        filter_planets: список имён транзитных планет для фильтрации (None = все)
        filter_aspects: список имён аспектов для фильтрации (None = все)

    Возвращает:
        список событий транзитов, отсортированных по дате
    """

    if settings is None:
        settings = DEFAULT_SETTINGS

    events = []

    # Определяем список аспектов с учётом фильтрации
    enabled_aspects = set(settings.get("enabled_aspects", DEFAULT_SETTINGS.get("enabled_aspects", [])))
    if filter_aspects is not None and len(filter_aspects) > 0:
        enabled_aspects = enabled_aspects.intersection(set(filter_aspects))

    # Определяем список транзитных планет с учётом фильтрации
    transit_planets = settings.get("transit_planets", DEFAULT_TRANSIT_PLANETS)
    if filter_planets is not None and len(filter_planets) > 0:
        transit_planets = [p for p in transit_planets if p in filter_planets]

    # Преобразуем даты в Julian Day
    start_local, start_utc = parse_local_datetime(start_date, "00:00", 0)
    end_local, end_utc = parse_local_datetime(end_date, "23:59", 0)
    jd_start = datetime_to_jd(start_utc)
    jd_end = datetime_to_jd(end_utc)

    # Для каждой транзитной планеты
    for planet_name in transit_planets:
        step_days = get_step_for_planet(planet_name)

        # Для каждой натальной точки
        for natal_obj in natal_objects:
            if "longitude" not in natal_obj or "name" not in natal_obj:
                continue

            natal_lon = natal_obj["longitude"]
            natal_name = natal_obj["name"]

            # Для каждого аспекта
            for aspect_def in ASPECT_DEFINITIONS:
                aspect_name = aspect_def["name"]
                if aspect_name not in enabled_aspects:
                    continue

                aspect_angle = aspect_def["angle"]

                # Получаем целевые долготы для этого аспекта
                target_lons = get_aspect_target_longitudes(natal_lon, aspect_angle)

                # Для каждой целевой долготы
                for target_lon in target_lons:
                    # Находим все пересечения целевой долготы за период
                    crossings = find_longitude_crossings(
                        jd_start, jd_end, planet_name, target_lon, step_days,
                        settings=settings
                    )

                    # Для каждого пересечения создаём событие
                    for jd in crossings:
                        # Определяем направление движения по скорости планеты
                        _, speed = get_planet_position(jd, planet_name, settings)
                        direction = "retrograde" if speed < 0 else "direct"

                        # Преобразуем Julian Day в читаемую дату
                        exact_dt = jd_to_datetime(jd)

                        event = {
                            "transit_planet": planet_name,
                            "natal_point": natal_name,
                            "aspect": aspect_name,
                            "target_longitude": round(target_lon, 6),
                            "exact_jd": jd,
                            "exact_datetime": exact_dt.isoformat(),
                            "direction": direction,
                            "orb": 0.0,
                        }

                        events.append(event)

    # Сортируем события по дате
    events.sort(key=lambda e: e["exact_jd"])

    return events


def find_orb_boundary(exact_jd, planet_name, target_longitude, max_orb,
                      direction="backward", max_days=60, settings=None):
    """
    Находит момент, когда транзитная планета входит в орб или выходит из орба.

    Параметры:
        exact_jd: Julian Day точного аспекта
        planet_name: имя транзитной планеты
        target_longitude: целевая долгота аспекта
        max_orb: максимальный орб аспекта
        direction: "backward" (вход в орб) или "forward" (выход из орба)
        max_days: максимальное число дней для поиска границы
        settings: настройки расчёта (для поддержки сидерического зодиака)

    Возвращает:
        Julian Day момента входа/выхода из орба
    """
    step_days = 0.25  # 6 часов
    if direction == "backward":
        step_days = -step_days

    jd = exact_jd
    prev_jd = exact_jd

    # Максимальное число шагов
    max_steps = int(max_days / abs(step_days))

    for _ in range(max_steps):
        prev_jd = jd
        jd += step_days

        # Получаем долготу планеты
        lon, _ = get_planet_position(jd, planet_name, settings)

        # Вычисляем разницу с целевой долготой
        angle_diff = abs(normalize_diff(lon - target_longitude))

        # Если разница углов больше max_orb, мы вышли из орба
        if angle_diff > max_orb:
            # Уточняем границу через бинарный поиск
            # prev_jd - внутри орба, jd - вне орба
            low = min(prev_jd, jd)
            high = max(prev_jd, jd)
            boundary_jd = refine_orb_boundary(low, high, planet_name, target_longitude,
                                              max_orb, settings=settings)
            return boundary_jd

    # Если не нашли границу за max_days, возвращаем точную дату
    # Это может произойти для очень медленных планет с большим орбом
    return exact_jd


def refine_orb_boundary(jd_low, jd_high, planet_name, target_longitude, max_orb,
                        max_iterations=50, settings=None):
    """
    Уточняет момент входа/выхода из орба через бинарный поиск.

    Параметры:
        jd_low: Julian Day, где планета внутри орба (angle_diff <= max_orb)
        jd_high: Julian Day, где планета вне орба (angle_diff > max_orb)
        planet_name: имя транзитной планеты
        target_longitude: целевая долгота аспекта
        max_orb: максимальный орб аспекта
        max_iterations: максимальное число итераций
        settings: настройки расчёта (для поддержки сидерического зодиака)

    Возвращает:
        Julian Day момента входа/выхода из орба
    """
    for _ in range(max_iterations):
        jd_mid = (jd_low + jd_high) / 2.0

        # Получаем долготу планеты в средней точке
        lon_mid, _ = get_planet_position(jd_mid, planet_name, settings)
        angle_diff_mid = abs(normalize_diff(lon_mid - target_longitude))

        # Если разница углов близка к max_orb, нашли границу
        if abs(angle_diff_mid - max_orb) < 1e-9:
            return jd_mid

        # Получаем разницу углов в нижней точке
        lon_low, _ = get_planet_position(jd_low, planet_name, settings)
        angle_diff_low = abs(normalize_diff(lon_low - target_longitude))

        # Если в jd_low разница углов меньше max_orb, то граница между jd_low и jd_mid
        if angle_diff_low < max_orb:
            jd_low = jd_mid
        else:
            jd_high = jd_mid

    return (jd_low + jd_high) / 2.0


def find_transit_periods(natal_objects, start_date, end_date, settings=None,
                         filter_planets=None, filter_aspects=None):
    """
    Находит периоды активности транзитов за период.

    Для каждого аспекта возвращает:
        - start_datetime: момент входа в орб
        - exact_datetime: момент точного аспекта (пик)
        - end_datetime: момент выхода из орба

    Параметры:
        natal_objects: список объектов натальной карты
        start_date: начальная дата (ГГГГ-ММ-ДД)
        end_date: конечная дата (ГГГГ-ММ-ДД)
        settings: настройки расчёта
        filter_planets: список имён транзитных планет для фильтрации (None = все)
        filter_aspects: список имён аспектов для фильтрации (None = все)

    Возвращает:
        список периодов активности транзитов, отсортированных по дате пика
    """

    if settings is None:
        settings = DEFAULT_SETTINGS

    # Сначала находим все точные аспекты с учётом фильтрации
    events = find_transit_events(
        natal_objects, start_date, end_date, settings,
        filter_planets=filter_planets, filter_aspects=filter_aspects
    )

    # Получаем орбы для аспектов
    orbs = settings.get("orbs", DEFAULT_SETTINGS.get("orbs", {}))

    periods = []

    for event in events:
        planet_name = event["transit_planet"]
        target_lon = event["target_longitude"]
        exact_jd = event["exact_jd"]
        aspect_name = event["aspect"]

        # Получаем max_orb для этого аспекта
        max_orb = float(orbs.get(aspect_name, 0.0))
        if max_orb <= 0.0:
            continue

        # Находим вход в орб (сканируем назад от точной даты)
        start_jd = find_orb_boundary(
            exact_jd, planet_name, target_lon, max_orb,
            direction="backward", settings=settings
        )

        # Находим выход из орба (сканируем вперёд от точной даты)
        end_jd = find_orb_boundary(
            exact_jd, planet_name, target_lon, max_orb,
            direction="forward", settings=settings
        )

        # Преобразуем в datetime
        start_dt = jd_to_datetime(start_jd)
        end_dt = jd_to_datetime(end_jd)

        # Формируем период активности
        period = {
            "transit_planet": event["transit_planet"],
            "natal_point": event["natal_point"],
            "aspect": event["aspect"],
            "target_longitude": event["target_longitude"],
            "direction": event["direction"],
            "start_jd": start_jd,
            "start_datetime": start_dt.isoformat(),
            "exact_jd": exact_jd,
            "exact_datetime": event["exact_datetime"],
            "end_jd": end_jd,
            "end_datetime": end_dt.isoformat(),
            "orb": max_orb,
        }

        periods.append(period)

    # Сортируем периоды по дате пика
    periods.sort(key=lambda p: p["exact_jd"])

    return periods