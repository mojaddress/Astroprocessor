from pathlib import Path

from .constants import (
    AYANAMSHA_SYSTEMS,
    DEFAULT_AYANAMSHA,
    SIGNS,
    HOUSE_SYSTEM_CODES,
)
from .utils import normalize_longitude, sign_from_longitude

try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
    SWISSEPH_IMPORT_ERROR = ""
except Exception as exc:
    swe = None
    SWISSEPH_AVAILABLE = False
    SWISSEPH_IMPORT_ERROR = str(exc)


# ============================================================
# Список планет для расчёта
# ============================================================

PLANET_NAMES = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]


def ensure_swisseph():
    """
    Проверяет, что Swiss Ephemeris доступен.
    """
    if not SWISSEPH_AVAILABLE:
        raise RuntimeError(
            "Swiss Ephemeris is not installed. "
            "Install with: py -3.11 -m pip install pyswisseph"
        )


def initialize_ephemeris(settings):
    """
    Указывает Swiss Ephemeris папку с файлами эфемерид.

    Разные версии pyswisseph могут называть функцию по-разному:
    - set_ephe_path
    - set_ephem_path
    - swe_set_ephe_path
    - swe_set_ephem_path

    Поэтому проверяем несколько вариантов.
    """
    if not SWISSEPH_AVAILABLE:
        return

    ephe_path = settings.get("ephe_path")
    if not ephe_path:
        return

    path = Path(ephe_path).expanduser()
    if not path.exists():
        return

    path_str = str(path)

    candidate_function_names = (
        "set_ephe_path",
        "set_ephem_path",
        "swe_set_ephe_path",
        "swe_set_ephem_path",
    )

    for func_name in candidate_function_names:
        func = getattr(swe, func_name, None)
        if callable(func):
            func(path_str)
            return


def get_planet_id(name):
    """
    Возвращает числовой идентификатор планеты или точки
    для Swiss Ephemeris.
    """
    mapping = {
        "Sun": getattr(swe, "SUN", 0),
        "Moon": getattr(swe, "MOON", 1),
        "Mercury": getattr(swe, "MERCURY", 2),
        "Venus": getattr(swe, "VENUS", 3),
        "Mars": getattr(swe, "MARS", 4),
        "Jupiter": getattr(swe, "JUPITER", 5),
        "Saturn": getattr(swe, "SATURN", 6),
        "Uranus": getattr(swe, "URANUS", 7),
        "Neptune": getattr(swe, "NEPTUNE", 8),
        "Pluto": getattr(swe, "PLUTO", 9),
        "MeanNode": getattr(swe, "MEAN_NODE", 10),
        "TrueNode": getattr(swe, "TRUE_NODE", 11),
        "Chiron": getattr(swe, "CHIRON", 15),
    }

    if name not in mapping:
        raise ValueError(f"Unknown celestial object: {name}")

    return int(mapping[name])


def setup_zodiac_mode(settings):
    """
    Настраивает режим зодиака (тропический или сидерический).

    Возвращает:
        (flags, warnings)
        flags - флаги для расчёта
        warnings - список предупреждений
    """
    warnings = []

    # Используем ключ "zodiac" (совместимо с существующими настройками проекта)
    zodiac_type = settings.get("zodiac", "tropical")
    ayanamsha = settings.get("ayanamsha", DEFAULT_AYANAMSHA)

    flags = getattr(swe, "FLG_SPEED", 256)

    if zodiac_type == "sidereal":
        # Получаем ID ayanamsha из констант
        ayanamsha_info = AYANAMSHA_SYSTEMS.get(ayanamsha)
        if not ayanamsha_info:
            warnings.append(
                f"Неизвестная система ayanamsha: {ayanamsha}. "
                f"Используется {DEFAULT_AYANAMSHA}."
            )
            ayanamsha_info = AYANAMSHA_SYSTEMS.get(DEFAULT_AYANAMSHA)

        if ayanamsha_info:
            ayanamsha_id = ayanamsha_info.get("swisseph_id", 1)

            try:
                # Устанавливаем режим сидерического зодиака
                set_sid_mode_func = getattr(swe, "set_sid_mode", None)
                if callable(set_sid_mode_func):
                    set_sid_mode_func(ayanamsha_id)
                    # Добавляем флаг сидерического зодиака
                    flags = flags | getattr(swe, "FLG_SIDEREAL", 2)
                else:
                    warnings.append(
                        "Функция set_sid_mode недоступна в этой версии "
                        "pyswisseph. Используется тропический зодиак."
                    )
            except Exception as e:
                warnings.append(f"Не удалось установить сидерический режим: {e}")
        else:
            warnings.append(
                f"Система ayanamsha {DEFAULT_AYANAMSHA} не найдена. "
                "Используется тропический зодиак."
            )
    else:
        # Для тропического зодиака сбрасываем режим сидерического зодиака
        try:
            set_sid_mode_func = getattr(swe, "set_sid_mode", None)
            if callable(set_sid_mode_func):
                set_sid_mode_func(0)  # 0 = тропический зодиак
        except Exception:
            pass

    return flags, warnings


def calculate_objects(julian_day, settings=None):
    """
    Рассчитывает положения планет и дополнительных точек.

    Параметры:
        julian_day: Julian Day
        settings: настройки расчёта (словарь)

    Настройки могут содержать:
        include_chiron: включать ли Хирон (по умолчанию True)
        include_nodes: включать ли лунные узлы (по умолчанию True)
        house_system: система домов (по умолчанию "placidus")
        node_type: тип узлов - "mean" или "true" (по умолчанию "mean")
        ephe_path: путь к файлам эфемерид (опционально)
        zodiac: тип зодиака - "tropical" или "sidereal" (по умолчанию "tropical")
        ayanamsha: система ayanamsha для сидерического зодиака (по умолчанию "lahiri")

    Возвращает:
        (objects, warnings)
        objects - список объектов (планеты, узлы, Хирон)
        warnings - список предупреждений
    """
    ensure_swisseph()

    if settings is None:
        settings = {}

    include_chiron = settings.get("include_chiron", True)
    include_nodes = settings.get("include_nodes", True)
    node_type = settings.get("node_type", "mean")

    warnings = []

    # Установка пути к эфемеридам
    initialize_ephemeris(settings)

    # Настройка режима зодиака
    flags, zodiac_warnings = setup_zodiac_mode(settings)
    warnings.extend(zodiac_warnings)

    objects = []

    # Рассчитываем планеты
    for planet_name in PLANET_NAMES:
        try:
            planet_id = get_planet_id(planet_name)
            result = swe.calc_ut(julian_day, planet_id, flags)
            coords = result[0]

            longitude = normalize_longitude(float(coords[0]))
            speed_longitude = float(coords[3]) if len(coords) > 3 else 0.0

            # Определяем ретроградность
            is_retrograde = speed_longitude < 0

            # Определяем знак и градус в знаке
            sign, degree_in_sign = sign_from_longitude(longitude)

            obj = {
                "name": planet_name,
                "type": "planet",
                "longitude": round(longitude, 6),
                "sign": sign,
                "degree_in_sign": round(degree_in_sign, 6),
                "speed_longitude": round(speed_longitude, 6),
                "retrograde": is_retrograde,
            }

            objects.append(obj)

        except Exception as e:
            warnings.append(f"Не удалось рассчитать {planet_name}: {e}")

    # Рассчитываем лунные узлы
    if include_nodes:
        try:
            node_name = "MeanNode" if node_type == "mean" else "TrueNode"
            node_id = get_planet_id(node_name)
            result = swe.calc_ut(julian_day, node_id, flags)
            coords = result[0]

            longitude = normalize_longitude(float(coords[0]))
            speed_longitude = float(coords[3]) if len(coords) > 3 else 0.0
            is_retrograde = speed_longitude < 0

            sign, degree_in_sign = sign_from_longitude(longitude)

            obj = {
                "name": node_name,
                "type": "point",
                "longitude": round(longitude, 6),
                "sign": sign,
                "degree_in_sign": round(degree_in_sign, 6),
                "speed_longitude": round(speed_longitude, 6),
                "retrograde": is_retrograde,
            }

            objects.append(obj)

        except Exception as e:
            warnings.append(f"Не удалось рассчитать лунные узлы: {e}")

    # Рассчитываем Хирон
    if include_chiron:
        try:
            chiron_id = get_planet_id("Chiron")
            result = swe.calc_ut(julian_day, chiron_id, flags)
            coords = result[0]

            longitude = normalize_longitude(float(coords[0]))
            speed_longitude = float(coords[3]) if len(coords) > 3 else 0.0
            is_retrograde = speed_longitude < 0

            sign, degree_in_sign = sign_from_longitude(longitude)

            obj = {
                "name": "Chiron",
                "type": "point",
                "longitude": round(longitude, 6),
                "sign": sign,
                "degree_in_sign": round(degree_in_sign, 6),
                "speed_longitude": round(speed_longitude, 6),
                "retrograde": is_retrograde,
            }

            objects.append(obj)

        except Exception as e:
            warnings.append(f"Не удалось рассчитать Хирон: {e}")

    return objects, warnings


def calculate_houses(julian_day, latitude, longitude, settings):
    """
    Рассчитывает дома, ASC и MC.

    Возвращает:
        houses, asc_longitude, mc_longitude
    """
    ensure_swisseph()

    house_system = settings.get("house_system", "placidus").lower()
    house_code = HOUSE_SYSTEM_CODES.get(house_system, "P")

    try:
        try:
            cusps, ascmc = swe.houses(
                julian_day,
                float(latitude),
                float(longitude),
                house_code.encode("ascii"),
            )
        except TypeError:
            cusps, ascmc = swe.houses(
                julian_day,
                float(latitude),
                float(longitude),
                house_code,
            )
    except Exception as error:
        raise RuntimeError(f"House calculation failed: {error}") from error

    # Swiss Ephemeris может вернуть 13 значений, где индекс 0 служебный.
    if len(cusps) == 13:
        cusp_values = list(cusps[1:])
    else:
        cusp_values = list(cusps[:12])

    houses = []
    for index, cusp_longitude in enumerate(cusp_values):
        normalized = normalize_longitude(float(cusp_longitude))
        sign, degree_in_sign = sign_from_longitude(normalized)
        houses.append(
            {
                "house": index + 1,
                "longitude": round(normalized, 6),
                "sign": sign,
                "degree_in_sign": round(degree_in_sign, 6),
            }
        )

    asc_longitude = normalize_longitude(float(ascmc[0]))
    mc_longitude = normalize_longitude(float(ascmc[1]))

    return houses, asc_longitude, mc_longitude


def get_planet_position(julian_day, planet_name, settings=None):
    """
    Возвращает долготу и скорость планеты.

    Это более лёгкая функция, чем calculate_objects,
    когда нужна только одна планета.

    Параметры:
        julian_day: Julian Day
        planet_name: имя планеты
        settings: настройки расчёта (опционально)

    Настройки могут содержать:
        zodiac: тип зодиака - "tropical" или "sidereal" (по умолчанию "tropical")
        ayanamsha: система ayanamsha для сидерического зодиака (по умолчанию "lahiri")
        ephe_path: путь к файлам эфемерид (опционально)

    Возвращает:
        (longitude, speed_longitude)
    """
    ensure_swisseph()

    if settings is None:
        settings = {}

    # Установка пути к эфемеридам
    initialize_ephemeris(settings)

    # Настройка режима зодиака
    flags, _ = setup_zodiac_mode(settings)

    planet_id = get_planet_id(planet_name)

    result = swe.calc_ut(julian_day, planet_id, flags)
    coords = result[0]

    longitude = normalize_longitude(float(coords[0]))
    speed_longitude = float(coords[3]) if len(coords) > 3 else 0.0

    return longitude, speed_longitude