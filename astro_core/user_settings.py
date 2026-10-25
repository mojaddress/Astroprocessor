"""
Настройки пользователя: config/user_settings.json (итерация 33).
Безопасные дефолты, устойчивое чтение, атомарная запись.
Путь можно переопределить переменной окружения ASTRO_USER_SETTINGS_PATH (тесты).
"""
import json
import os
import tempfile
from typing import Dict

DEFAULTS: Dict = {
    "ephemeris_path": "ephe",
    "default_display_profile": "full",
    "default_transit_city": "",
}


def _path() -> str:
    env = os.environ.get("ASTRO_USER_SETTINGS_PATH")
    if env:
        return env
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "config", "user_settings.json")


def load_user_settings() -> Dict:
    data = dict(DEFAULTS)
    try:
        with open(_path(), encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            for k, v in loaded.items():
                data[k] = v
    except (OSError, ValueError):
        pass
    return data


def save_user_settings(data: Dict) -> None:
    p = _path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in (data or {}).items()})
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except OSError:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
