"""
Тесты интеграции профилей отображения с расчётом натальной карты (шаг 2.2).

Проверяют:
- обратную совместимость (без профиля всё как раньше);
- фильтрацию планет через enabled_planets;
- интеграцию встроенных профилей;
- корректное поведение Part of Fortune при исключённой Луне;
- переопределение орбов.

Примечание: Хирон и астероиды требуют файлы эфемерид (ephe/seas_18.se1).
Без настройки ephe_path Swiss Ephemeris использует встроенную эфемериду
Мошье, которая покрывает планеты Солнце–Плутон и лунные узлы, но НЕ Хирон.
Тесты, которым нужен Хирон, защищены пропуском при отсутствии папки ephe/.
"""

from pathlib import Path

import pytest

from astro_core.chart import build_natal_chart, _filter_enabled_planets
from astro_core.ephemeris import SWISSEPH_AVAILABLE
from astro_core import display_profiles as dp


DEMO_BIRTH = {
    "name": "Demo Person",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
}

# Корень проекта и папка эфемерид (абсолютный путь, не зависит от места запуска)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EPHE_DIR = PROJECT_ROOT / "ephe"

pytestmark = pytest.mark.skipif(
    not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed"
)


# ============================================================
# Модульные тесты фильтра (эфемериды не нужны, быстрые и детерминированные)
# ============================================================

def test_filter_keeps_points_and_angles():
    """Фильтр убирает только планеты; точки и углы остаются."""
    objects = [
        {"name": "Sun", "type": "planet"},
        {"name": "Jupiter", "type": "planet"},
        {"name": "Chiron", "type": "point"},
        {"name": "MeanNode", "type": "point"},
        {"name": "ASC", "type": "angle"},
    ]
    filtered = _filter_enabled_planets(objects, ["Sun"])
    names = {o["name"] for o in filtered}
    assert names == {"Sun", "Chiron", "MeanNode", "ASC"}


def test_filter_none_disables_filtering():
    """enabled_planets=None — список возвращается без изменений."""
    objects = [
        {"name": "Sun", "type": "planet"},
        {"name": "Jupiter", "type": "planet"},
    ]
    assert _filter_enabled_planets(objects, None) is objects


def test_filter_empty_list_removes_all_planets():
    """Пустой enabled_planets — все планеты убраны, точки остались."""
    objects = [
        {"name": "Sun", "type": "planet"},
        {"name": "Chiron", "type": "point"},
    ]
    filtered = _filter_enabled_planets(objects, [])
    names = {o["name"] for o in filtered}
    assert names == {"Chiron"}


# ============================================================
# Интеграционные тесты (нужен Swiss Ephemeris)
# ============================================================

def test_all_planets_by_default():
    """Без enabled_planets рассчитываются все 10 планет (обратная совместимость)."""
    result = build_natal_chart(DEMO_BIRTH, {})
    planet_names = {p["name"] for p in result["planets"] if p.get("type") == "planet"}
    assert len(planet_names) == 10
    assert "Uranus" in planet_names


def test_enabled_planets_filters_planets():
    """enabled_planets исключает планеты из результата."""
    settings = {"enabled_planets": ["Sun", "Moon", "Mercury"]}
    result = build_natal_chart(DEMO_BIRTH, settings)
    planet_names = {p["name"] for p in result["planets"] if p.get("type") == "planet"}
    assert planet_names == {"Sun", "Moon", "Mercury"}


def test_enabled_planets_does_not_affect_nodes():
    """Фильтр не трогает лунные узлы — у них свой флаг include_nodes."""
    settings = {"enabled_planets": ["Sun", "Moon"]}
    result = build_natal_chart(DEMO_BIRTH, settings)
    names = {p["name"] for p in result["planets"]}
    assert "MeanNode" in names


@pytest.mark.skipif(not EPHE_DIR.exists(), reason="Папка эфемерид ephe/ не найдена")
def test_chiron_kept_with_ephe_path():
    """
    С указанным путём к эфемеридам Хирон рассчитывается,
    и фильтр планет его не убирает (у Хирона тип 'point').
    """
    settings = {
        "enabled_planets": ["Sun", "Moon"],
        "ephe_path": str(EPHE_DIR),
    }
    result = build_natal_chart(DEMO_BIRTH, settings)
    names = {p["name"] for p in result["planets"]}
    assert "MeanNode" in names
    assert "Chiron" in names


def test_classic_profile_integration():
    """Классический профиль: без внешних планет, Хирона и узлов."""
    profile = dp.get_builtin_profile("classic")
    settings = dp.apply_profile_to_settings(profile)
    result = build_natal_chart(DEMO_BIRTH, settings)
    names = {p["name"] for p in result["planets"]}
    assert "Uranus" not in names
    assert "Neptune" not in names
    assert "Pluto" not in names
    assert "Chiron" not in names
    assert "MeanNode" not in names
    assert "Sun" in names
    assert "Saturn" in names


def test_minimal_profile_integration():
    """Минимальный профиль: только личные планеты и углы."""
    profile = dp.get_builtin_profile("minimal")
    settings = dp.apply_profile_to_settings(profile)
    result = build_natal_chart(DEMO_BIRTH, settings)
    planet_names = {p["name"] for p in result["planets"] if p.get("type") == "planet"}
    assert planet_names == {"Sun", "Moon", "Mercury", "Venus", "Mars"}
    additional_names = {p["name"] for p in result["additional_points"]}
    assert "ASC" in additional_names
    assert "MC" in additional_names


def test_aspects_only_between_enabled_objects():
    """Аспекты строятся только между включёнными объектами."""
    settings = {
        "enabled_planets": ["Sun", "Moon"],
        "include_chiron": False,
        "include_nodes": False,
    }
    result = build_natal_chart(DEMO_BIRTH, settings)
    allowed = {"Sun", "Moon", "ASC", "MC", "PartOfFortune"}
    for aspect in result["aspects"]:
        assert aspect["point_a"] in allowed, f"Лишняя точка в аспекте: {aspect['point_a']}"
        assert aspect["point_b"] in allowed, f"Лишняя точка в аспекте: {aspect['point_b']}"


def test_pof_skipped_when_moon_disabled():
    """Если Луна исключена, Part of Fortune не рассчитывается, выдаётся предупреждение."""
    settings = {"enabled_planets": ["Sun", "Mercury"]}
    result = build_natal_chart(DEMO_BIRTH, settings)
    additional_names = {p["name"] for p in result["additional_points"]}
    assert "PartOfFortune" not in additional_names
    assert any("Part of Fortune" in w for w in result["warnings"])


def test_profile_orb_overrides_applied():
    """Переопределение орбов из профиля применяется к аспектам."""
    profile = dp.get_builtin_profile("full")
    profile["aspects"]["conjunction"]["orb"] = 0.0001
    settings = dp.apply_profile_to_settings(profile)
    result = build_natal_chart(DEMO_BIRTH, settings)
    for aspect in result["aspects"]:
        if aspect["aspect"] == "conjunction":
            assert aspect["orb"] <= 0.0001


def test_full_profile_matches_default_chart():
    """Полный профиль даёт тот же набор планет, что и карта без профиля."""
    profile = dp.get_builtin_profile("full")
    settings = dp.apply_profile_to_settings(profile)
    result = build_natal_chart(DEMO_BIRTH, settings)
    planet_names = {p["name"] for p in result["planets"] if p.get("type") == "planet"}
    assert len(planet_names) == 10

def test_chiron_computed_by_default():
    """
    Микро-шаг 2.2.1: Хирон рассчитывается по умолчанию,
    потому что путь к эфемеридам задан в constants.py
    и не зависит от папки, из которой запущена программа.
    """
    result = build_natal_chart(DEMO_BIRTH, {})
    names = {p["name"] for p in result["planets"]}
    assert "Chiron" in names
    assert not any("Хирон" in w for w in result["warnings"])