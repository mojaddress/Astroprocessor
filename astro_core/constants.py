SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

ASPECT_DEFINITIONS = [
    {"name": "conjunction", "angle": 0.0},
    {"name": "sextile", "angle": 60.0},
    {"name": "square", "angle": 90.0},
    {"name": "trine", "angle": 120.0},
    {"name": "opposition", "angle": 180.0},
]

HOUSE_SYSTEM_CODES = {
    "placidus": "P",
    "koch": "K",
    "equal": "E",
    "whole_sign": "W",
    "porphyry": "O",
    "regiomontanus": "R",
    "campanus": "C",
}

DEFAULT_SETTINGS = {
    "zodiac": "tropical",
    "house_system": "placidus",
    "node_type": "mean",
    "include_chiron": True,
    "include_nodes": True,
    "include_part_of_fortune": True,
    "include_angles": True,
    "ephe_path": None,
    "enabled_aspects": [
        "conjunction",
        "sextile",
        "square",
        "trine",
        "opposition",
    ],
    "orbs": {
        "conjunction": 8.0,
        "opposition": 8.0,
        "square": 6.0,
        "trine": 6.0,
        "sextile": 4.0,
    },
}
# ============================================================
# Русские названия для отображения в интерфейсе
# ============================================================

# Русские названия планет и точек
PLANET_NAMES_RU = {
    "Sun": "Солнце",
    "Moon": "Луна",
    "Mercury": "Меркурий",
    "Venus": "Венера",
    "Mars": "Марс",
    "Jupiter": "Юпитер",
    "Saturn": "Сатурн",
    "Uranus": "Уран",
    "Neptune": "Нептун",
    "Pluto": "Плутон",
    "MeanNode": "Средний Узел",
    "TrueNode": "Истинный Узел",
    "Chiron": "Хирон",
    "ASC": "Асцендент",
    "MC": "Середина Неба",
    "PartOfFortune": "Колесо Фортуны",
}

# Русские названия знаков зодиака
SIGN_NAMES_RU = {
    "Aries": "Овен",
    "Taurus": "Телец",
    "Gemini": "Близнецы",
    "Cancer": "Рак",
    "Leo": "Лев",
    "Virgo": "Дева",
    "Libra": "Весы",
    "Scorpio": "Скорпион",
    "Sagittarius": "Стрелец",
    "Capricorn": "Козерог",
    "Aquarius": "Водолей",
    "Pisces": "Рыбы",
}

# Русские названия аспектов
ASPECT_NAMES_RU = {
    "conjunction": "Соединение",
    "sextile": "Секстиль",
    "square": "Квадрат",
    "trine": "Трин",
    "opposition": "Оппозиция",
}

# Русские названия типов объектов
OBJECT_TYPE_NAMES_RU = {
    "planet": "Планета",
    "angle": "Угол",
    "point": "Точка",
}

# Русские названия направлений движения
DIRECTION_NAMES_RU = {
    "direct": "Директное",
    "retrograde": "Ретроградное",
}


def get_planet_name_ru(name):
    """Возвращает русское название планеты или точки."""
    return PLANET_NAMES_RU.get(name, name)


def get_sign_name_ru(name):
    """Возвращает русское название знака зодиака."""
    return SIGN_NAMES_RU.get(name, name)


def get_aspect_name_ru(name):
    """Возвращает русское название аспекта."""
    return ASPECT_NAMES_RU.get(name, name)


def get_object_type_name_ru(name):
    """Возвращает русское название типа объекта."""
    return OBJECT_TYPE_NAMES_RU.get(name, name)


def get_direction_name_ru(name):
    """Возвращает русское название направления движения."""
    return DIRECTION_NAMES_RU.get(name, name)

# ============================================================
# Списки объектов для расчётов
# ============================================================

# Планеты, которые по умолчанию используются как транзитные.
# Этот список можно переопределить через настройки или фильтрацию.
DEFAULT_TRANSIT_PLANETS = [
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

# ============================================================
# Типы зодиака и ayanamsha
# ============================================================

# Типы зодиака
ZODIAC_TYPES = {
    "tropical": "Тропический",
    "sidereal": "Сидерический",
}

# Системы ayanamsha (сдвиг между тропическим и сидерическим зодиаком)
# Значения ID соответствуют константам Swiss Ephemeris
AYANAMSHA_SYSTEMS = {
    "lahiri": {
        "name": "Lahiri",
        "name_ru": "Лахири",
        "description": "Стандарт в ведической астрологии (Индия)",
        "swisseph_id": 1,
    },
    "raman": {
        "name": "Raman",
        "name_ru": "Раман",
        "description": "Альтернативная ведическая система",
        "swisseph_id": 3,
    },
    "krishnamurti": {
        "name": "Krishnamurti",
        "name_ru": "Кришнамурти",
        "description": "Система Кришнамурти (KP)",
        "swisseph_id": 5,
    },
    "fagan_brady": {
        "name": "Fagan-Bradley",
        "name_ru": "Фаган-Брэдли",
        "description": "Западная сидерическая астрология",
        "swisseph_id": 0,
    },
}

# Система ayanamsha по умолчанию
DEFAULT_AYANAMSHA = "lahiri"


def get_ayanamsha_name_ru(ayanamsha_key):
    """Возвращает русское название системы ayanamsha."""
    system = AYANAMSHA_SYSTEMS.get(ayanamsha_key)
    if system:
        return system["name_ru"]
    return ayanamsha_key