"""Итерация 33: настройки пользователя."""
from astro_core import user_settings as us


def test_load_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_USER_SETTINGS_PATH", str(tmp_path / "u.json"))
    cfg = us.load_user_settings()
    assert cfg["ephemeris_path"] == "ephe"
    assert cfg["default_display_profile"] == "full"


def test_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_USER_SETTINGS_PATH", str(tmp_path / "u.json"))
    us.save_user_settings({"ephemeris_path": "my_ephe"})
    cfg = us.load_user_settings()
    assert cfg["ephemeris_path"] == "my_ephe"
    assert cfg["default_display_profile"] == "full"


def test_corrupt_json_falls_back_to_defaults(tmp_path, monkeypatch):
    p = tmp_path / "u.json"
    p.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv("ASTRO_USER_SETTINGS_PATH", str(p))
    assert us.load_user_settings() == us.DEFAULTS
