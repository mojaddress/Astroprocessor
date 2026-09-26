"""
Тесты модуля профилей отображения.
"""

import pytest

from astro_core import display_profiles as dp


def test_builtin_profiles_exist():
    profiles = dp.get_builtin_profiles()
    for name in dp.BUILTIN_PROFILE_NAMES:
        assert name in profiles


def test_builtin_profiles_valid():
    for name, profile in dp.get_builtin_profiles().items():
        errors = dp.validate_profile(profile)
        assert errors == [], f"Профиль {name} некорректен: {errors}"


def test_full_profile_has_all_objects():
    full = dp.get_builtin_profile("full")
    for key in dp.ALL_OBJECT_KEYS:
        assert full["objects"][key] is True


def test_classic_profile_disables_outers():
    classic = dp.get_builtin_profile("classic")
    assert classic["objects"]["Uranus"] is False
    assert classic["objects"]["Neptune"] is False
    assert classic["objects"]["Pluto"] is False
    assert classic["objects"]["Chiron"] is False
    assert classic["objects"]["Sun"] is True


def test_minimal_profile_only_personal():
    minimal = dp.get_builtin_profile("minimal")
    for p in ("Sun", "Moon", "Mercury", "Venus", "Mars"):
        assert minimal["objects"][p] is True
    assert minimal["objects"]["Jupiter"] is False
    assert minimal["objects"]["Angles"] is True


def test_apply_profile_to_settings():
    profile = dp.get_builtin_profile("classic")
    settings = dp.apply_profile_to_settings(profile)
    assert settings["include_chiron"] is False
    assert settings["include_nodes"] is False
    assert "Uranus" not in settings["enabled_planets"]
    assert "Sun" in settings["enabled_planets"]
    assert set(settings["enabled_aspects"]) == set(dp.ALL_ASPECTS)


def test_apply_profile_orb_override():
    profile = dp.get_builtin_profile("full")
    profile["aspects"]["conjunction"]["orb"] = 10.0
    settings = dp.apply_profile_to_settings(profile)
    assert settings["orbs"]["conjunction"] == 10.0


def test_apply_profile_disables_aspect():
    profile = dp.get_builtin_profile("full")
    profile["aspects"]["sextile"]["enabled"] = False
    settings = dp.apply_profile_to_settings(profile)
    assert "sextile" not in settings["enabled_aspects"]
    assert "sextile" not in settings["orbs"]


def test_save_load_roundtrip(tmp_path):
    profile = dp.get_builtin_profile("full")
    profile["name"] = "Мой профиль"
    dp.save_display_profile(profile, dir_path=tmp_path)
    loaded = dp.load_display_profile("Мой профиль", dir_path=tmp_path)
    assert loaded["name"] == "Мой профиль"
    assert loaded["objects"] == profile["objects"]
    assert "created_at" in loaded


def test_load_builtin_profile():
    profile = dp.load_display_profile("classic")
    assert profile["name"] == "classic"


def test_load_missing_profile(tmp_path):
    with pytest.raises(FileNotFoundError):
        dp.load_display_profile("nonexistent", dir_path=tmp_path)


def test_list_display_profiles_includes_builtin(tmp_path):
    profiles = dp.list_display_profiles(dir_path=tmp_path)
    names = [p["name"] for p in profiles]
    for builtin in dp.BUILTIN_PROFILE_NAMES:
        assert builtin in names


def test_delete_builtin_not_allowed(tmp_path):
    assert dp.delete_display_profile("classic", dir_path=tmp_path) is False


def test_delete_user_profile(tmp_path):
    profile = dp.get_builtin_profile("full")
    profile["name"] = "Временный"
    dp.save_display_profile(profile, dir_path=tmp_path)
    assert dp.delete_display_profile("Временный", dir_path=tmp_path) is True
    with pytest.raises(FileNotFoundError):
        dp.load_display_profile("Временный", dir_path=tmp_path)


def test_corrupted_file_skipped(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{invalid json", encoding="utf-8")
    profiles = dp.list_display_profiles(dir_path=tmp_path)
    names = [p["name"] for p in profiles]
    assert "full" in names  # встроенные на месте, битый файл пропущен


def test_validate_profile_rejects_bad_orb():
    profile = dp.get_builtin_profile("full")
    profile["aspects"]["conjunction"]["orb"] = 999
    errors = dp.validate_profile(profile)
    assert len(errors) > 0


def test_validate_profile_rejects_unknown_object():
    profile = dp.get_builtin_profile("full")
    profile["objects"]["FakePlanet"] = True
    errors = dp.validate_profile(profile)
    assert any("FakePlanet" in e for e in errors)


def test_get_appearance_fills_defaults():
    profile = dp.get_builtin_profile("full")
    profile["appearance"] = {"chart_size": 1000}
    appearance = dp.get_appearance(profile)
    assert appearance["chart_size"] == 1000
    assert appearance["label_mode"] == "symbols"  # значение по умолчанию