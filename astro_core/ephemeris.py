from pathlib import Path

from .constants import (
    AYANAMSHA_SYSTEMS,
    DEFAULT_AYANAMSHA,
    SIGNS,
    HOUSE_SYSTEM_CODES,
)
from .utils import normalize_longitude, sign_from_longitude
import functools  # CACHE_INTEGRATION_V1
from . import ephemeris_cache  # CACHE_INTEGRATION_V1


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

# ASTEROIDS_V1: основные астероиды (файл эфемерид seas_18.se1).
ASTEROID_NAMES = ["Ceres", "Pallas", "Juno", "Vesta"]


# --- Интеграция кэша эфемерид --- CACHE_INTEGRATION_V1
def _ephemeris_state(args, kwargs):
    """Снимок настроек, влияющих на глобальное состояние Swiss Ephemeris."""
    settings = None
    for value in args:
        if isinstance(value, dict):
            settings = value
            break
    if settings is None:
        settings = kwargs.get("settings")
    settings = settings or {}
    zodiac = str(settings.get("zodiac", "tropical")).lower()
    ayanamsha = settings.get("ayanamsha", settings.get("ayanamsha_id", ""))
    ephe_path = str(settings.get("ephe_path", ""))
    return {"zodiac": zodiac, "ayanamsha": repr(ayanamsha), "ephe_path": ephe_path}


def _invalidates_ephemeris_cache(func):
    """Сбрасывает кэш ТОЛЬКО при изменении зодиака/аянамши/пути эфемерид.  # CACHE_STATE_V2

    initialize_ephemeris и setup_zodiac_mode вызываются на каждом расчёте,
    поэтому безусловный сброс уничтожал кэш (0% попаданий, только накладные).
    set_context сам сравнивает контекст и очищает кэш лишь при изменении.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global _ACTIVE_CONTEXT
        _ACTIVE_CONTEXT = None
        state = _ephemeris_state(args, kwargs)
        try:
            ephemeris_cache.set_context(**state)
        except RuntimeError:
            # Swiss Ephemeris недоступен: кэш не создан, сбрасывать нечего.
            pass
        return func(*args, **kwargs)
    return wrapper


_cached_calc_ut = ephemeris_cache.calc_ut

# --- Кэш активного контекста эфемерид --- CALL_PATH_V1
# Путь эфемерид и режим зодиака - глобальное состояние Swiss Ephemeris.
# Пересчитывать их на каждый вызов дорого (замер: 87.5% стоимости вызова).
# Контекст переустанавливается только при смене сигнатуры настроек.
_ACTIVE_CONTEXT = None
_ACTIVE_FLAGS = None
_ACTIVE_WARNINGS = ()



def ensure_swisseph():
    """
    Проверяет, что Swiss Ephemeris доступен.
    """
    if not SWISSEPH_AVAILABLE:
        raise RuntimeError(
            "Swiss Ephemeris is not installed. "
            "Install with: py -3.11 -m pip install pyswisseph"
        )


@_invalidates_ephemeris_cache
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


@functools.lru_cache(maxsize=64)  # CALL_PATH_V1: id планет постоянны
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
        # ASTEROIDS_V1
        "Ceres": getattr(swe, "CERES", 17),
        "Pallas": getattr(swe, "PALLAS", 18),
        "Juno": getattr(swe, "JUNO", 19),
        "Vesta": getattr(swe, "VESTA", 20),
    }

    if name not in mapping:
        raise ValueError(f"Unknown celestial object: {name}")

    return int(mapping[name])


@_invalidates_ephemeris_cache
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


def _ensure_context(settings):
    """Гарантирует нужный контекст эфемерид; возвращает (flags, warnings).  # CALL_PATH_V1

    Повторные вызовы с теми же настройками не трогают глобальное состояние
    Swiss Ephemeris и не пересчитывают снимок настроек. Смена зодиака,
    аянамши или пути эфемерид переустанавливает контекст полностью.
    Прямые вызовы initialize_ephemeris/setup_zodiac_mode сбрасывают кэш
    через декоратор, поэтому рассинхронизация невозможна.
    """
    global _ACTIVE_CONTEXT, _ACTIVE_FLAGS, _ACTIVE_WARNINGS
    config = settings or {}
    signature = (
        str(config.get("zodiac", "tropical")).lower(),
        repr(config.get("ayanamsha", DEFAULT_AYANAMSHA)),
        str(config.get("ephe_path", "")),
    )
    if _ACTIVE_CONTEXT == signature:
        return _ACTIVE_FLAGS, list(_ACTIVE_WARNINGS)

    initialize_ephemeris(config)
    flags, warnings = setup_zodiac_mode(config)
    _ACTIVE_CONTEXT = signature
    _ACTIVE_FLAGS = flags
    _ACTIVE_WARNINGS = tuple(warnings)
    return flags, list(_ACTIVE_WARNINGS)


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

    # Контекст кэшируется по сигнатуре настроек (CALL_PATH_V1).
    flags, zodiac_warnings = _ensure_context(settings)
    warnings.extend(zodiac_warnings)

    objects = []

    # Рассчитываем планеты
    for planet_name in PLANET_NAMES:
        try:
            planet_id = get_planet_id(planet_name)
            result = _cached_calc_ut(julian_day, planet_id, flags)
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
            result = _cached_calc_ut(julian_day, node_id, flags)
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

            # Нисходящий (Южный) узел всегда в 180° от Восходящего (Северного).
            south_longitude = normalize_longitude(longitude + 180.0)
            south_sign, south_degree = sign_from_longitude(south_longitude)
            south_obj = {
                "name": "SouthNode",
                "type": "point",
                "longitude": round(south_longitude, 6),
                "sign": south_sign,
                "degree_in_sign": round(south_degree, 6),
                "speed_longitude": round(speed_longitude, 6),
                "retrograde": is_retrograde,
            }
            objects.append(south_obj)

        except Exception as e:
            warnings.append(f"Не удалось рассчитать лунные узлы: {e}")

    # Рассчитываем Хирон
    if include_chiron:
        try:
            chiron_id = get_planet_id("Chiron")
            result = _cached_calc_ut(julian_day, chiron_id, flags)
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

    # --- Астероиды --- ASTEROIDS_V1
    if settings.get("include_asteroids", False):
        for asteroid_name in ASTEROID_NAMES:
            try:
                asteroid_id = get_planet_id(asteroid_name)
                result = _cached_calc_ut(julian_day, asteroid_id, flags)
                coords = result[0]
                longitude = normalize_longitude(float(coords[0]))
                speed_longitude = float(coords[3]) if len(coords) > 3 else 0.0
                sign, degree_in_sign = sign_from_longitude(longitude)
                objects.append({
                    "name": asteroid_name,
                    "type": "asteroid",
                    "longitude": round(longitude, 6),
                    "sign": sign,
                    "degree_in_sign": round(degree_in_sign, 6),
                    "speed_longitude": round(speed_longitude, 6),
                    "retrograde": speed_longitude < 0,
                })
            except Exception as exc:
                warnings.append(
                    f"{asteroid_name}: недоступен ({exc}). "
                    f"Нужен файл эфемерид seas_18.se1 - см. менеджер эфемерид.")

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

    # Контекст кэшируется по сигнатуре настроек (CALL_PATH_V1).
    flags, _ = _ensure_context(settings)

    planet_id = get_planet_id(planet_name)

    result = _cached_calc_ut(julian_day, planet_id, flags)
    coords = result[0]

    longitude = normalize_longitude(float(coords[0]))
    speed_longitude = float(coords[3]) if len(coords) > 3 else 0.0

    return longitude, speed_longitude


def calculate_vertex(julian_day, latitude, longitude, settings):
    """Вертекс - точка западного горизонта в прима-вертикали (VXMP).

    Swiss Ephemeris возвращает её в ascmc[3]. Отдельная функция сохраняет
    контракт calculate_houses (он возвращает только дома, ASC и MC).
    """
    ensure_swisseph()
    house_system = (settings or {}).get("house_system", "placidus").lower()
    house_code = HOUSE_SYSTEM_CODES.get(house_system, "P")
    try:
        try:
            _cusps, ascmc = swe.houses(
                julian_day, float(latitude), float(longitude),
                house_code.encode("ascii"))
        except TypeError:
            _cusps, ascmc = swe.houses(
                julian_day, float(latitude), float(longitude), house_code)
    except Exception as error:
        raise RuntimeError(f"Vertex calculation failed: {error}") from error
    if len(ascmc) < 4:
        raise RuntimeError("Vertex calculation failed: ascmc too short")
    return normalize_longitude(float(ascmc[3]))


def calculate_hypothetical_point(julian_day, name, settings=None):
    """Точки русской школы: Лилит (средний апогей), Селена, Прозерпина.

    Селена и Прозерпина требуют файл seorbel.txt в папке эфемерид;
    при его отсутствии возвращается None (итерация 39, D-82).
    """
    ids = {"BlackMoon": ("MEAN_APOGEE", 12),
           "Selena": ("WHITE_MOON", 56),
           "Proserpina": ("PROSERPINA", 57)}
    if name not in ids:
        return None
    attr, fallback = ids[name]
    body_id = getattr(swe, attr, fallback)
    flags, _ = _ensure_context(settings)  # CALL_PATH_V1
    try:
        result = _cached_calc_ut(julian_day, body_id, flags)
    except Exception:
        return None
    coords = result[0]
    longitude = normalize_longitude(float(coords[0]))
    speed = float(coords[3]) if len(coords) > 3 else 0.0
    sign, degree_in_sign = sign_from_longitude(longitude)
    return {
        "name": name,
        "type": "point",
        "longitude": round(longitude, 6),
        "sign": sign,
        "degree_in_sign": round(degree_in_sign, 6),
        "speed_longitude": round(speed, 6),
        "retrograde": speed < 0,
    }
