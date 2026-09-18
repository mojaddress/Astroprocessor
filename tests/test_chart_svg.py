"""
Тесты для модуля графического отображения карты в SVG.

Проверяют:
- корректность преобразования координат;
- валидность генерируемого SVG;
- режимы подписей (символы, слова, оба);
- зум и смещение;
- устойчивость к пустым данным.
"""

import pytest

from astro_core.chart import build_natal_chart
from astro_core.chart_svg import (
    longitude_to_svg_coords,
    render_natal_chart_svg,
)
from astro_core.ephemeris import SWISSEPH_AVAILABLE


@pytest.fixture
def natal_chart():
    """Фикстура: создаёт натальную карту один раз для всех тестов."""
    birth = {
        "name": "Test",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "utc_offset_hours": 3,
    }
    natal_settings = {"include_chiron": False, "include_nodes": False}
    return build_natal_chart(birth, natal_settings)


# ============================================================
# Тесты преобразования координат
# ============================================================

def test_longitude_to_svg_coords_aries():
    """0° Овна должно быть слева (на 9 часах)."""
    cx, cy = 400, 400
    radius = 100
    x, y = longitude_to_svg_coords(0, radius, cx, cy)
    # Слева: x < cx, y = cy
    assert x < cx
    assert abs(y - cy) < 1e-6


def test_longitude_to_svg_coords_cancer():
    """90° Рака должно быть вверху (на 12 часах)."""
    cx, cy = 400, 400
    radius = 100
    x, y = longitude_to_svg_coords(90, radius, cx, cy)
    # Вверху: x = cx, y < cy
    assert abs(x - cx) < 1e-6
    assert y < cy


def test_longitude_to_svg_coords_libra():
    """180° Весов должно быть справа (на 3 часах)."""
    cx, cy = 400, 400
    radius = 100
    x, y = longitude_to_svg_coords(180, radius, cx, cy)
    # Справа: x > cx, y = cy
    assert x > cx
    assert abs(y - cy) < 1e-6


def test_longitude_to_svg_coords_capricorn():
    """270° Козерога должно быть внизу (на 6 часах)."""
    cx, cy = 400, 400
    radius = 100
    x, y = longitude_to_svg_coords(270, radius, cx, cy)
    # Внизу: x = cx, y > cy
    assert abs(x - cx) < 1e-6
    assert y > cy


# ============================================================
# Тесты генерации SVG
# ============================================================

@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_returns_valid_svg(natal_chart):
    """Проверка, что функция возвращает валидный SVG."""
    svg = render_natal_chart_svg(natal_chart)
    assert svg.startswith('<svg')
    assert svg.strip().endswith('</svg>')


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_contains_circles(natal_chart):
    """Проверка, что SVG содержит круги."""
    svg = render_natal_chart_svg(natal_chart)
    assert '<circle' in svg


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_contains_planets(natal_chart):
    """Проверка, что SVG содержит планеты."""
    svg = render_natal_chart_svg(natal_chart)
    # Проверяем наличие хотя бы одной точки планеты
    assert 'planet-dot' in svg


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_contains_signs(natal_chart):
    """Проверка, что SVG содержит знаки зодиака."""
    svg = render_natal_chart_svg(natal_chart, label_mode="symbols")
    # Проверяем наличие хотя бы одного символа знака
    assert '♈' in svg  # Овен


# ============================================================
# Тесты режимов подписей
# ============================================================

@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_label_mode_symbols(natal_chart):
    """Проверка режима 'только символы'."""
    svg = render_natal_chart_svg(natal_chart, label_mode="symbols")
    assert svg.startswith('<svg')
    # В режиме символов должен быть символ Солнца
    assert '☉' in svg


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_label_mode_words(natal_chart):
    """Проверка режима 'только слова'."""
    svg = render_natal_chart_svg(natal_chart, label_mode="words")
    assert svg.startswith('<svg')
    # В режиме слов должно быть слово "Солнце"
    assert 'Солнце' in svg


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_label_mode_both(natal_chart):
    """Проверка режима 'символы + слова'."""
    svg = render_natal_chart_svg(natal_chart, label_mode="both")
    assert svg.startswith('<svg')
    # В режиме 'оба' должны быть и символ, и слово
    assert '☉' in svg
    assert 'Солнце' in svg


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_default_is_symbols(natal_chart):
    """Проверка, что режим по умолчанию — 'только символы'."""
    svg = render_natal_chart_svg(natal_chart)
    assert svg.startswith('<svg')
    # По умолчанию должен быть символ Солнца
    assert '☉' in svg


# ============================================================
# Тесты зума и смещения
# ============================================================

@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_zoom(natal_chart):
    """Проверка, что зум меняет viewBox."""
    svg_normal = render_natal_chart_svg(natal_chart, zoom=1.0)
    svg_zoomed = render_natal_chart_svg(natal_chart, zoom=2.0)

    # SVG должен быть разным
    assert svg_normal != svg_zoomed
    # В увеличенной версии должен быть viewBox
    assert 'viewBox' in svg_zoomed


@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_offset(natal_chart):
    """Проверка, что смещение меняет viewBox."""
    svg_normal = render_natal_chart_svg(natal_chart, offset_x=0, offset_y=0)
    svg_offset = render_natal_chart_svg(natal_chart, offset_x=100, offset_y=100)

    # SVG должен быть разным
    assert svg_normal != svg_offset


# ============================================================
# Тесты аспектов
# ============================================================

@pytest.mark.skipif(not SWISSEPH_AVAILABLE, reason="Swiss Ephemeris is not installed")
def test_render_svg_aspects_toggle(natal_chart):
    """Проверка, что аспекты можно отключить."""
    svg_with = render_natal_chart_svg(natal_chart, show_aspects=True)
    svg_without = render_natal_chart_svg(natal_chart, show_aspects=False)

    # SVG должен быть разным
    assert svg_with != svg_without


# ============================================================
# Тесты устойчивости к пустым данным
# ============================================================

def test_render_svg_empty_data():
    """Проверка, что пустые данные не ломают функцию."""
    empty_data = {
        "birth": {"name": "Empty"},
        "planets": [],
        "houses": [],
        "aspects": [],
        "additional_points": [],
    }
    svg = render_natal_chart_svg(empty_data)
    assert svg.startswith('<svg')
    assert svg.strip().endswith('</svg>')


def test_render_svg_missing_fields():
    """Проверка, что отсутствующие поля не ломают функцию."""
    minimal_data = {
        "birth": {"name": "Minimal"},
    }
    svg = render_natal_chart_svg(minimal_data)
    assert svg.startswith('<svg')
    assert svg.strip().endswith('</svg>')