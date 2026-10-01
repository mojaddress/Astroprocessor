"""
Тесты интеграции профилей отображения с рендерингом SVG (шаг 2.3).

Не требуют Swiss Ephemeris: используется синтетическая карта.
"""

from astro_core import display_profiles as dp
from astro_core.chart_svg import (
    render_natal_chart_svg,
    render_transit_chart_svg,
)
from astro_core.constants import SIGNS


def _demo_chart():
    """Синтетическая карта для тестов рендеринга (эфемериды не нужны)."""
    return {
        "birth": {"name": "Test"},
        "planets": [
            {"name": "Sun", "longitude": 10.0, "sign": "Aries",
             "retrograde": False, "speed_longitude": 0.9},
            {"name": "Moon", "longitude": 100.0, "sign": "Cancer",
             "retrograde": False, "speed_longitude": 13.0},
        ],
        "additional_points": [],
        "houses": [
            {"house": i + 1, "longitude": i * 30.0,
             "sign": SIGNS[i], "degree_in_sign": 0.0}
            for i in range(12)
        ],
        "aspects": [
            {"point_a": "Sun", "point_b": "Moon", "aspect": "square",
             "angle": 90.0, "orb": 0.0, "max_orb": 6.0, "strength": 1.0}
        ],
        "warnings": [],
    }


def _demo_transits():
    transit_planets = [
        {"name": "Mars", "longitude": 200.0, "sign": "Libra",
         "retrograde": False, "speed_longitude": 0.5},
    ]
    transit_aspects = [
        {"transit_planet": "Mars", "natal_point": "Sun", "aspect": "opposition",
         "angle": 180.0, "orb": 1.0, "max_orb": 8.0, "strength": 0.9}
    ]
    return transit_planets, transit_aspects


# ============================================================
# Совместимость get_render_kwargs с функциями отрисовки
# ============================================================

def test_render_kwargs_compatible_with_natal_render():
    """get_render_kwargs распаковывается в render_natal_chart_svg без ошибок."""
    profile = dp.get_builtin_profile("full")
    svg = render_natal_chart_svg(_demo_chart(), **dp.get_render_kwargs(profile))
    assert svg.startswith("<svg")


def test_render_kwargs_compatible_with_transit_render():
    """get_render_kwargs распаковывается в render_transit_chart_svg без ошибок."""
    profile = dp.get_builtin_profile("full")
    transit_planets, transit_aspects = _demo_transits()
    svg = render_transit_chart_svg(
        _demo_chart(), transit_planets, transit_aspects,
        **dp.get_render_kwargs(profile)
    )
    assert svg.startswith("<svg")


# ============================================================
# Новые возможности рендеринга
# ============================================================

def test_show_houses_false_removes_house_numbers():
    """При show_houses=False исчезают 12 подписей номеров домов."""
    chart = _demo_chart()
    svg_with = render_natal_chart_svg(chart, show_houses=True)
    svg_without = render_natal_chart_svg(chart, show_houses=False)
    texts_with = svg_with.count("<text")
    texts_without = svg_without.count("<text")
    assert texts_with - texts_without == 12


def test_planet_colors_override():
    """Переопределение цвета планеты из профиля попадает в SVG."""
    svg = render_natal_chart_svg(_demo_chart(), planet_colors={"Sun": "#123456"})
    assert "#123456" in svg


def test_aspect_colors_override():
    """Переопределение цвета аспекта из профиля попадает в SVG."""
    svg = render_natal_chart_svg(_demo_chart(), aspect_colors={"square": "#ABCDEF"})
    assert "#ABCDEF" in svg


def test_planet_dot_size_applied():
    """Размер точек планет применяется."""
    svg = render_natal_chart_svg(_demo_chart(), planet_dot_size=9)
    assert 'r="9"' in svg


def test_profile_appearance_end_to_end():
    """Профиль с настройками внешнего вида применяется через get_render_kwargs."""
    profile = dp.get_builtin_profile("full")
    profile["appearance"]["planet_colors"] = {"Sun": "#00FF00"}
    profile["appearance"]["planet_dot_size"] = 7
    svg = render_natal_chart_svg(_demo_chart(), **dp.get_render_kwargs(profile))
    assert "#00FF00" in svg
    assert 'r="7"' in svg


def test_default_render_backward_compatible():
    """Старый вызов без новых параметров работает как раньше."""
    svg = render_natal_chart_svg(_demo_chart(), size=600, show_aspects=True,
                                 label_mode="symbols")
    assert svg.startswith("<svg")
    assert 'r="5"' in svg  # размер точек по умолчанию