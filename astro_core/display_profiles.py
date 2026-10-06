"""
Модуль профилей отображения.

Профиль отображения — это сохранённый набор настроек того, какие объекты
и аспекты рассчитываются и отображаются, а также как выглядит карта.

Модуль покрывает полный функционал кастомизации (Вариант C):
- включение/исключение планет и точек из расчётов и отображения;
- включение/исключение аспектов и переопределение их орбов;
- внешний вид: режим подписей, цвета, размеры, дома, линии аспектов.

Встроенные профили (classic, vedic, minimal, full) не хранятся на диске.
Пользовательские профили хранятся в папке config/display_profiles/ как JSON.
"""

import json
import copy
import re
from datetime import datetime, timezone
from pathlib import Path

from .constants import DEFAULT_SETTINGS

# ============================================================
# Канонические списки объектов и аспектов
# ============================================================

# Все индивидуальные планеты
ALL_PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
]

# Специальные ключи объектов (не индивидуальные планеты)
SPECIAL_OBJECTS = ["Chiron", "LunarNodes", "PartOfFortune", "Angles"]

# Все ключи объектов, доступные в профиле
ALL_OBJECT_KEYS = ALL_PLANETS + SPECIAL_OBJECTS

# Все аспекты (соответствует ASPECT_DEFINITIONS в constants.py)
ALL_ASPECTS = ["conjunction", "sextile", "square", "trine", "opposition"]

# Орбы по умолчанию (совпадают с DEFAULT_SETTINGS)
DEFAULT_ORBS = {
    "conjunction": 8.0,
    "opposition": 8.0,
    "square": 6.0,
    "trine": 6.0,
    "sextile": 4.0,
}

# Папка хранения пользовательских профилей
DEFAULT_DISPLAY_PROFILES_DIR = "config/display_profiles"

# Имена встроенных профилей
BUILTIN_PROFILE_NAMES = ["classic", "vedic", "minimal", "full"]

# Допустимые режимы подписей
VALID_LABEL_MODES = ["symbols", "words", "both"]


# ============================================================
# Конструкторы частей профиля
# ============================================================

def _all_objects_enabled():
    """Все объекты включены."""
    return {key: True for key in ALL_OBJECT_KEYS}


def _all_aspects_enabled():
    """Все аспекты включены с орбами по умолчанию."""
    return {
        name: {"enabled": True, "orb": DEFAULT_ORBS[name]}
        for name in ALL_ASPECTS
    }


def _default_appearance():
    """Настройки внешнего вида по умолчанию."""
    return {
        "label_mode": "symbols",
        "show_houses": True,
        "show_aspect_lines": True,
        "chart_size": 800,
        "planet_dot_size": 5,
        "planet_colors": {},   # пусто = использовать цвета из chart_svg
        "aspect_colors": {},   # пусто = использовать цвета из chart_svg
        "show_planet_labels": True,
        "show_asteroid_labels": True,
        "show_node_labels": True,
        "show_angle_labels": True,
    }


def build_profile(name, description="", objects=None, aspects=None, appearance=None):
    """
    Собирает профиль отображения.

    Параметры:
        name: имя профиля
        description: описание
        objects: словарь {ключ_объекта: bool} или None (все включены)
        aspects: словарь {аспект: {enabled, orb}} или None (все включены)
        appearance: словарь внешнего вида или None (по умолчанию)

    Возвращает:
        словарь профиля
    """
    return {
        "name": name,
        "description": description,
        "objects": objects if objects is not None else _all_objects_enabled(),
        "aspects": aspects if aspects is not None else _all_aspects_enabled(),
        "appearance": appearance if appearance is not None else _default_appearance(),
    }


# ============================================================
# Встроенные профили
# ============================================================

def get_builtin_profiles():
    """
    Возвращает словарь встроенных профилей.

    Возвращает:
        {имя: профиль}
    """
    # Классический: традиционные планеты Солнце–Сатурн,
    # без внешних планет, без Хирона, но с лунными узлами.
    classic_objects = _all_objects_enabled()
    for outer in ("Uranus", "Neptune", "Pluto"):
        classic_objects[outer] = False
    classic_objects["Chiron"] = False
    classic_objects["LunarNodes"] = True

    # Ведический: Солнце–Сатурн + лунные узлы (Раху/Кету),
    # без внешних планет и Хирона.
    vedic_objects = _all_objects_enabled()
    for outer in ("Uranus", "Neptune", "Pluto"):
        vedic_objects[outer] = False
    vedic_objects["Chiron"] = False
    vedic_objects["LunarNodes"] = True

    # Минимальный: только личные планеты + углы.
    minimal_objects = {key: False for key in ALL_OBJECT_KEYS}
    for p in ("Sun", "Moon", "Mercury", "Venus", "Mars"):
        minimal_objects[p] = True
    minimal_objects["Angles"] = True

    return {
        "classic": build_profile(
            "classic",
            "Классическая карта: традиционные планеты Солнце–Сатурн",
            objects=classic_objects,
        ),
        "vedic": build_profile(
            "vedic",
            "Ведическая карта: Солнце–Сатурн и лунные узлы",
            objects=vedic_objects,
        ),
        "minimal": build_profile(
            "minimal",
            "Минимальная карта: только личные планеты",
            objects=minimal_objects,
        ),
        "full": build_profile(
            "full",
            "Полная карта: все объекты и аспекты",
        ),
    }


def get_builtin_profile(name):
    """Возвращает встроенный профиль по имени или None."""
    return get_builtin_profiles().get(name)


# ============================================================
# Хранение пользовательских профилей
# ============================================================

def get_display_profiles_dir(dir_path=None):
    """Возвращает путь к папке профилей как объект Path."""
    if dir_path is None:
        dir_path = DEFAULT_DISPLAY_PROFILES_DIR
    return Path(dir_path)


def profile_to_filename(profile_name):
    """Преобразует имя профиля в безопасное имя файла."""
    safe = re.sub(r'[^\w\s\-]', '', profile_name, flags=re.UNICODE)
    safe = safe.strip()
    safe = re.sub(r'\s+', '_', safe)
    safe = safe[:50]
    if not safe:
        safe = "display_profile"
    return safe + ".json"


def save_display_profile(profile, dir_path=None):
    """
    Сохраняет пользовательский профиль в файл.

    Возвращает:
        Путь к сохранённому файлу (Path)

    Исключения:
        ValueError: если у профиля нет имени
    """
    if "name" not in profile or not str(profile["name"]).strip():
        raise ValueError("Display profile must have a name")

    dirp = get_display_profiles_dir(dir_path)
    dirp.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    to_save = copy.deepcopy(profile)
    to_save["updated_at"] = now
    if "created_at" not in to_save:
        to_save["created_at"] = now

    filename = profile_to_filename(profile["name"])
    file_path = dirp / filename
    file_path.write_text(
        json.dumps(to_save, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return file_path


def load_display_profile(name, dir_path=None):
    """
    Загружает профиль по имени. Сначала ищет среди встроенных,
    затем среди пользовательских файлов.

    Исключения:
        FileNotFoundError: если профиль не найден
    """
    builtin = get_builtin_profile(name)
    if builtin is not None:
        return copy.deepcopy(builtin)

    dirp = get_display_profiles_dir(dir_path)
    file_path = dirp / profile_to_filename(name)
    if not file_path.exists():
        raise FileNotFoundError(f"Display profile not found: {name}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def list_display_profiles(dir_path=None):
    """
    Возвращает список всех профилей: сначала встроенные,
    затем пользовательские. Повреждённые файлы пропускаются.
    """
    result = []

    for _name, prof in get_builtin_profiles().items():
        p = copy.deepcopy(prof)
        p["_builtin"] = True
        result.append(p)

    dirp = get_display_profiles_dir(dir_path)
    if dirp.exists():
        for file_path in sorted(dirp.glob("*.json")):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                data["_filename"] = file_path.name
                data["_builtin"] = False
                result.append(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

    return result


def delete_display_profile(name, dir_path=None):
    """
    Удаляет пользовательский профиль. Встроенные удалить нельзя.

    Возвращает:
        True, если профиль удалён, иначе False
    """
    if name in BUILTIN_PROFILE_NAMES:
        return False

    dirp = get_display_profiles_dir(dir_path)
    file_path = dirp / profile_to_filename(name)
    if file_path.exists():
        file_path.unlink()
        return True
    return False


# ============================================================
# Преобразование профиля в настройки расчёта
# ============================================================

def apply_profile_to_settings(profile, base_settings=None):
    """
    Применяет профиль к настройкам расчёта, которые понимает chart.py.

    Параметры:
        profile: профиль отображения
        base_settings: базовые настройки (или None для DEFAULT_SETTINGS)

    Возвращает:
        новый словарь настроек с применённым профилем
    """
    settings = copy.deepcopy(base_settings if base_settings is not None else DEFAULT_SETTINGS)

    objects = profile.get("objects", {})
    settings["include_chiron"] = bool(objects.get("Chiron", True))
    settings["include_nodes"] = bool(objects.get("LunarNodes", True))
    settings["include_part_of_fortune"] = bool(objects.get("PartOfFortune", True))
    settings["include_angles"] = bool(objects.get("Angles", True))
    settings["enabled_planets"] = [p for p in ALL_PLANETS if objects.get(p, True)]

    aspects = profile.get("aspects", {})
    enabled_aspects = []
    orbs = {}
    for aspect_name in ALL_ASPECTS:
        cfg = aspects.get(aspect_name, {})
        if cfg.get("enabled", True):
            enabled_aspects.append(aspect_name)
            orbs[aspect_name] = float(cfg.get("orb", DEFAULT_ORBS[aspect_name]))

    settings["enabled_aspects"] = enabled_aspects
    settings["orbs"] = orbs
    return settings


def get_appearance(profile):
    """
    Возвращает настройки внешнего вида с заполненными значениями
    по умолчанию для отсутствующих ключей.
    """
    appearance = _default_appearance()
    appearance.update(profile.get("appearance", {}))
    return appearance


# ============================================================
# Валидация профиля
# ============================================================

def validate_profile(profile):
    """
    Проверяет корректность профиля.

    Возвращает:
        список строк-ошибок (пустой список, если профиль корректен)
    """
    errors = []

    if not profile.get("name"):
        errors.append("Профиль должен иметь имя")

    objects = profile.get("objects", {})
    for key in objects:
        if key not in ALL_OBJECT_KEYS:
            errors.append(f"Неизвестный объект: {key}")

    aspects = profile.get("aspects", {})
    for name, cfg in aspects.items():
        if name not in ALL_ASPECTS:
            errors.append(f"Неизвестный аспект: {name}")
            continue
        orb = cfg.get("orb")
        if orb is not None:
            try:
                orb_value = float(orb)
            except (ValueError, TypeError):
                errors.append(f"Орб аспекта {name} не является числом: {orb}")
                continue
            if orb_value < 0 or orb_value > 30:
                errors.append(f"Орб аспекта {name} вне диапазона 0..30: {orb_value}")

    appearance = profile.get("appearance", {})
    label_mode = appearance.get("label_mode")
    if label_mode is not None and label_mode not in VALID_LABEL_MODES:
        errors.append(f"Недопустимый label_mode: {label_mode}")

    return errors

# ============================================================
# Параметры рендеринга для chart_svg
# ============================================================

def get_render_kwargs(profile):
    """
    Формирует готовые параметры отрисовки для функций chart_svg
    из настроек внешнего вида профиля.

    Использование:
        render_natal_chart_svg(chart_data, **get_render_kwargs(profile))
        render_transit_chart_svg(natal, transits, aspects, **get_render_kwargs(profile))

    Параметры:
        profile: профиль отображения

    Возвращает:
        словарь параметров для функций отрисовки
    """
    appearance = get_appearance(profile)
    return {
        "size": appearance["chart_size"],
        "show_aspects": appearance["show_aspect_lines"],
        "label_mode": appearance["label_mode"],
        "show_houses": appearance["show_houses"],
        "planet_dot_size": appearance["planet_dot_size"],
        "planet_colors": appearance["planet_colors"],
        "aspect_colors": appearance["aspect_colors"],
        "show_planet_labels": appearance.get("show_planet_labels", True),
        "show_asteroid_labels": appearance.get("show_asteroid_labels", True),
        "show_node_labels": appearance.get("show_node_labels", True),
        "show_angle_labels": appearance.get("show_angle_labels", True),
    }