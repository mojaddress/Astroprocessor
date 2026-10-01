"""
Модуль графического отображения натальной карты в формате SVG.

Рисует классическую астрологическую карту:
- круг знаков зодиака;
- круг домов;
- планеты;
- аспекты;
- маркеры ASC и MC.

Поддерживает:
- три режима подписей: слова, символы, оба варианта;
- масштабирование (зум);
- перемещение (панорамирование);
- настройку внешнего вида из профилей отображения (шаг 2.3):
  цвета планет и аспектов, размер точек, показ домов.

Режим подписей по умолчанию: "symbols" (только символы).

Важно:
    В астрологических картах 0° Овна обычно находится слева (на 9 часах),
    и зодиак идёт против часовой стрелки.
    В SVG координата Y растёт вниз, поэтому используется инверсия.
"""

import math
from xml.sax.saxutils import escape

from .constants import SIGNS, get_planet_name_ru, get_sign_name_ru

# ============================================================
# Настройки размеров
# ============================================================

DEFAULT_SIZE = 800

# Радиусы колец (доля от размера)
R_OUTER = 0.440
R_ZODIAC = 0.405
R_HOUSES = 0.370
R_PLANETS = 0.325
R_ASPECTS = 0.295

# Размер точки планеты по умолчанию
DEFAULT_PLANET_DOT_SIZE = 5

# Цвета для аспектов (палитра по умолчанию)
ASPECT_COLORS = {
    "conjunction": "#FF6B00",
    "sextile": "#2E86AB",
    "square": "#D62828",
    "trine": "#2A9D8F",
    "opposition": "#7B2D8B",
}

# Цвета планет (палитра по умолчанию)
PLANET_COLORS = {
    "Sun": "#FF9900",
    "Moon": "#757575",
    "Mercury": "#E6A800",
    "Venus": "#339933",
    "Mars": "#CC0000",
    "Jupiter": "#993399",
    "Saturn": "#000000",
    "Uranus": "#0099CC",
    "Neptune": "#006666",
    "Pluto": "#660000",
    "MeanNode": "#666666",
    "TrueNode": "#666666",
    "Chiron": "#996633",
}

FONT_FAMILY = "Segoe UI, Arial, sans-serif"
FONT_FAMILY_SYMBOLS = "Segoe UI Symbol, Segoe UI, Arial, sans-serif"

# ============================================================
# Отображаемые имена и символы
# ============================================================

PLANET_DISPLAY_NAMES = {
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
    "MeanNode": "Узел",
    "TrueNode": "Узел",
    "Chiron": "Хирон",
}

SIGN_DISPLAY_NAMES = {
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

SIGN_SYMBOLS = {
    "Aries": "♈",
    "Taurus": "♉",
    "Gemini": "♊",
    "Cancer": "♋",
    "Leo": "♌",
    "Virgo": "♍",
    "Libra": "♎",
    "Scorpio": "♏",
    "Sagittarius": "♐",
    "Capricorn": "♑",
    "Aquarius": "♒",
    "Pisces": "♓",
}

PLANET_SYMBOLS = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
    "MeanNode": "☊",
    "TrueNode": "☊",
    "Chiron": "⚷",
}

# Размеры шрифтов в зависимости от режима подписей
SIGN_FONT_SIZES = {
    "symbols": 18,
    "both": 14,
    "words": 12,
}

PLANET_FONT_SIZES = {
    "symbols": 22,
    "both": 16,
    "words": 12,
}

# ============================================================
# Параметры умного смещения планет при наложении
# ============================================================

MAX_PLANET_SHIFTS = 3
PLANET_SHIFT_STEP = 0.025
MIN_PLANET_RADIUS_RATIO = 0.25
PLANET_PROXIMITY_DEG = 5.0

# ============================================================
# Вспомогательные функции
# ============================================================

def longitude_to_svg_coords(longitude, radius, cx, cy):
    """
    Преобразует астрологическую долготу в координаты SVG.
    """
    angle_deg = 180.0 - longitude
    angle_rad = math.radians(angle_deg)

    x = cx + radius * math.cos(angle_rad)
    y = cy - radius * math.sin(angle_rad)

    return x, y


def _get_planet_label(planet_name, label_mode):
    """Возвращает подпись планеты в зависимости от режима."""
    word = PLANET_DISPLAY_NAMES.get(planet_name, get_planet_name_ru(planet_name))
    symbol = PLANET_SYMBOLS.get(planet_name, "")

    if label_mode == "symbols":
        return symbol if symbol else word
    elif label_mode == "both":
        return f"{symbol} {word}" if symbol else word
    else:
        return word


def _get_sign_label(sign_name, label_mode):
    """Возвращает подпись знака зодиака в зависимости от режима."""
    word = SIGN_DISPLAY_NAMES.get(sign_name, get_sign_name_ru(sign_name))
    symbol = SIGN_SYMBOLS.get(sign_name, "")

    if label_mode == "symbols":
        return symbol if symbol else word
    elif label_mode == "both":
        return f"{symbol} {word}" if symbol else word
    else:
        return word


def _is_symbol_mode(label_mode):
    """Проверяет, используются ли символы (для выбора шрифта)."""
    return label_mode in ("symbols", "both")


def _angular_diff(lon_a, lon_b):
    """Минимальная угловая разница между двумя долготами (0..180)."""
    diff = abs(lon_a - lon_b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def _resolve_planet_radius(lon, size, base_radius, used_positions):
    """
    Умное смещение планеты при наложении на уже размещённые планеты.

    Ограничено число смещений и минимальный радиус,
    чтобы планеты не выходили за пределы карты при большом стеллиуме.
    """
    radius = base_radius
    min_radius = size * MIN_PLANET_RADIUS_RATIO
    shifts = 0

    for used_lon, _used_radius in used_positions:
        if shifts >= MAX_PLANET_SHIFTS:
            break

        diff = _angular_diff(lon, used_lon)

        if diff < PLANET_PROXIMITY_DEG:
            candidate = radius - size * PLANET_SHIFT_STEP
            if candidate >= min_radius:
                radius = candidate
                shifts += 1

    return radius


def _merge_colors(default_palette, overrides):
    """
    Объединяет палитру по умолчанию с переопределениями из профиля.

    То, что не переопределено, берётся из палитры по умолчанию.
    """
    merged = dict(default_palette)
    if overrides:
        merged.update(overrides)
    return merged


# ============================================================
# Генераторы SVG-элементов
# ============================================================

def _svg_header(size, zoom, offset_x, offset_y):
    """Генерирует заголовок SVG с учётом зума и смещения."""
    cx = size / 2
    cy = size / 2

    view_size = size / zoom
    view_x = cx - view_size / 2 + offset_x
    view_y = cy - view_size / 2 + offset_y

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" '
        f'viewBox="{view_x:.2f} {view_y:.2f} {view_size:.2f} {view_size:.2f}" '
        f'style="background-color: white;">\n'
    )


def _svg_footer():
    """Генерирует завершение SVG."""
    return '</svg>\n'


def _svg_circle(cx, cy, r, stroke="black", stroke_width=1, fill="none",
                stroke_dasharray=None, opacity=1.0):
    """Генерирует круг."""
    dash = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
    return (
        f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"'
        f'{dash} opacity="{opacity}"/>\n'
    )


def _svg_line(x1, y1, x2, y2, stroke="black", stroke_width=1, opacity=1.0,
              stroke_dasharray=None):
    """Генерирует линию."""
    dash = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
    return (
        f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}"{dash} opacity="{opacity}"/>\n'
    )


def _svg_text(x, y, text, font_size=12, fill="black", anchor="middle",
              weight="normal", use_symbol_font=False):
    """Генерирует текст."""
    escaped_text = escape(str(text))
    font_family = FONT_FAMILY_SYMBOLS if use_symbol_font else FONT_FAMILY
    return (
        f'  <text x="{x:.2f}" y="{y:.2f}" '
        f'font-family="{font_family}" font-size="{font_size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">'
        f'{escaped_text}</text>\n'
    )


# ============================================================
# Главная функция рисования натальной карты
# ============================================================

def render_natal_chart_svg(chart_data, size=DEFAULT_SIZE, show_aspects=True,
                           label_mode="symbols", zoom=1.0, offset_x=0.0, offset_y=0.0,
                           show_houses=True, planet_dot_size=DEFAULT_PLANET_DOT_SIZE,
                           planet_colors=None, aspect_colors=None):
    """
    Рисует натальную карту в формате SVG.

    Параметры:
        chart_data: словарь с данными карты (результат build_natal_chart)
        size: размер SVG в пикселях
        show_aspects: отображать ли аспекты
        label_mode: режим подписей: "symbols", "words", "both"
        zoom: масштаб (1.0 = 100%)
        offset_x: смещение по горизонтали
        offset_y: смещение по вертикали
        show_houses: отображать ли дома (шаг 2.3)
        planet_dot_size: радиус точек планет (шаг 2.3)
        planet_colors: переопределение цветов планет (шаг 2.3)
        aspect_colors: переопределение цветов аспектов (шаг 2.3)

    Возвращает:
        строку с SVG-кодом
    """
    cx = size / 2
    cy = size / 2

    r_outer = size * R_OUTER
    r_zodiac = size * R_ZODIAC
    r_houses = size * R_HOUSES
    r_planets = size * R_PLANETS
    r_aspects = size * R_ASPECTS

    use_symbols = _is_symbol_mode(label_mode)
    sign_font_size = SIGN_FONT_SIZES.get(label_mode, 10)
    planet_font_size = PLANET_FONT_SIZES.get(label_mode, 9)

    # Палитры с учётом переопределений из профиля
    final_planet_colors = _merge_colors(PLANET_COLORS, planet_colors)
    final_aspect_colors = _merge_colors(ASPECT_COLORS, aspect_colors)

    svg_parts = []

    svg_parts.append(_svg_header(size, zoom, offset_x, offset_y))
    svg_parts.append(f'  <rect width="{size}" height="{size}" fill="white"/>\n')

    # 1. Круги
    svg_parts.append(_svg_circle(cx, cy, r_outer, stroke="black", stroke_width=2))
    svg_parts.append(_svg_circle(cx, cy, r_zodiac, stroke="black", stroke_width=1))
    svg_parts.append(_svg_circle(cx, cy, r_houses, stroke="black", stroke_width=0.5,
                                 stroke_dasharray="4,2"))
    svg_parts.append(_svg_circle(cx, cy, r_aspects, stroke="gray", stroke_width=0.5,
                                 stroke_dasharray="2,2"))

    # 2. Знаки зодиака
    for i, sign in enumerate(SIGNS):
        boundary_lon = i * 30.0
        x1, y1 = longitude_to_svg_coords(boundary_lon, r_zodiac, cx, cy)
        x2, y2 = longitude_to_svg_coords(boundary_lon, r_outer, cx, cy)
        svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="black", stroke_width=0.8))

        mid_lon = boundary_lon + 15.0
        x_text, y_text = longitude_to_svg_coords(mid_lon, (r_zodiac + r_outer) / 2, cx, cy)

        sign_label = _get_sign_label(sign, label_mode)
        svg_parts.append(_svg_text(
            x_text, y_text, sign_label,
            font_size=sign_font_size, fill="black", use_symbol_font=use_symbols
        ))

    # 3. Дома (отображаются, если включены профилем)
    houses = chart_data.get("houses", [])

    if houses and show_houses:
        for house in houses:
            cusp_lon = house.get("longitude")
            if cusp_lon is None:
                continue

            x1, y1 = longitude_to_svg_coords(cusp_lon, r_aspects, cx, cy)
            x2, y2 = longitude_to_svg_coords(cusp_lon, r_houses, cx, cy)

            lw = 1.5 if house.get("house") == 1 else 0.8
            svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="black", stroke_width=lw))

            house_number = house.get("house", 0)
            next_idx = house_number % len(houses)
            next_cusp_lon = houses[next_idx].get("longitude", cusp_lon)

            diff = (next_cusp_lon - cusp_lon) % 360
            mid_lon = (cusp_lon + diff / 2) % 360
            x_text, y_text = longitude_to_svg_coords(mid_lon, (r_aspects + r_houses) / 2, cx, cy)

            svg_parts.append(_svg_text(x_text, y_text, str(house_number),
                                       font_size=9, fill="gray"))

    # 4. Планеты (исправленный блок умного смещения)
    planets = chart_data.get("planets", [])
    planet_positions = {}

    sorted_planets = sorted(planets, key=lambda p: p.get("longitude", 0))
    used_positions = []

    for planet in sorted_planets:
        lon = planet.get("longitude")
        if lon is None:
            continue

        planet_name = planet.get("name", "?")

        radius = _resolve_planet_radius(lon, size, r_planets, used_positions)
        used_positions.append((lon, radius))

        x, y = longitude_to_svg_coords(lon, radius, cx, cy)
        planet_positions[planet_name] = (x, y)

        base_color = final_planet_colors.get(planet_name, "black")
        is_retrograde = planet.get("retrograde", False)

        dot_stroke = "#D62828" if is_retrograde else "none"
        dot_stroke_width = 1.5 if is_retrograde else 0

        # Подготавливаем данные для тултипов
        planet_ru = get_planet_name_ru(planet_name)
        sign_ru = get_sign_name_ru(planet.get("sign", ""))
        speed_lon = planet.get("speed_longitude", 0)

        svg_parts.append(
            f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{planet_dot_size}" fill="{base_color}" '
            f'stroke="{dot_stroke}" stroke-width="{dot_stroke_width}" '
            f'class="planet-dot" data-planet="{planet_ru}" '
            f'data-lon="{lon:.6f}" data-speed="{speed_lon:.6f}" '
            f'data-sign="{sign_ru}"/>\n'
        )

        planet_label = _get_planet_label(planet_name, label_mode)
        text_color = "black" if base_color in ("#000000", "#660000") else base_color

        x_label, y_label = longitude_to_svg_coords(lon, radius + size * 0.035, cx, cy)
        svg_parts.append(_svg_text(
            x_label, y_label, planet_label,
            font_size=planet_font_size, fill=text_color,
            use_symbol_font=use_symbols, weight="bold"
        ))

    # 5. ASC и MC
    additional_points = chart_data.get("additional_points", [])

    for point in additional_points:
        point_name = point.get("name")
        lon = point.get("longitude")

        if point_name is None or lon is None:
            continue

        if point_name == "ASC":
            x1, y1 = longitude_to_svg_coords(lon, r_houses, cx, cy)
            x2, y2 = longitude_to_svg_coords(lon, r_outer, cx, cy)
            svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="red", stroke_width=2))

            x_text, y_text = longitude_to_svg_coords(lon, r_outer + size * 0.035, cx, cy)
            svg_parts.append(_svg_text(x_text, y_text, "ASC",
                                       font_size=16, fill="red", weight="bold"))

        elif point_name == "MC":
            x1, y1 = longitude_to_svg_coords(lon, r_houses, cx, cy)
            x2, y2 = longitude_to_svg_coords(lon, r_outer, cx, cy)
            svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="blue", stroke_width=2))

            x_text, y_text = longitude_to_svg_coords(lon, r_outer + size * 0.035, cx, cy)
            svg_parts.append(_svg_text(x_text, y_text, "MC",
                                       font_size=16, fill="blue", weight="bold"))

    # 6. Аспекты (опционально)
    if show_aspects:
        aspects = chart_data.get("aspects", [])

        for aspect in aspects:
            point_a = aspect.get("point_a")
            point_b = aspect.get("point_b")
            aspect_name = aspect.get("aspect")

            if point_a in planet_positions and point_b in planet_positions:
                x1, y1 = planet_positions[point_a]
                x2, y2 = planet_positions[point_b]

                color = final_aspect_colors.get(aspect_name, "gray")
                svg_parts.append(_svg_line(x1, y1, x2, y2, stroke=color,
                                           stroke_width=0.8, opacity=0.7))

    svg_parts.append(_svg_footer())

    return ''.join(svg_parts)

# ============================================================
# Транзитная карта (двухкруговая)
# ============================================================

TR_OUTER = 0.440
TR_ZODIAC = 0.405
TR_TRANSIT = 0.360
TR_NATAL = 0.280
TR_ASPECTS = 0.240

COLOR_NATAL = "#2E86AB"
COLOR_TRANSIT = "#2A9D8F"


def render_transit_chart_svg(natal_chart, transit_planets, transit_aspects,
                             size=DEFAULT_SIZE, label_mode="symbols", show_aspects=True,
                             transit_houses=None, transit_additional_points=None,
                             show_houses=True, planet_dot_size=DEFAULT_PLANET_DOT_SIZE,
                             planet_colors=None, aspect_colors=None):
    """
    Рисует транзитную карту в формате SVG.

    Параметры:
        natal_chart: словарь с данными натальной карты
        transit_planets: список транзитных планет с долготами
        transit_aspects: список транзитных аспектов
        size: размер SVG в пикселях
        label_mode: режим подписей ("symbols", "words", "both")
        show_aspects: отображать ли аспекты
        transit_houses: дома транзита (опционально)
        transit_additional_points: углы транзита (ASC, MC, опционально)
        show_houses: отображать ли дома — натальные и транзитные (шаг 2.3)
        planet_dot_size: радиус точек планет (шаг 2.3)
        planet_colors: переопределение цветов планет (шаг 2.3)
        aspect_colors: переопределение цветов аспектов (шаг 2.3)

    Возвращает:
        строку с SVG-кодом
    """
    cx = size / 2
    cy = size / 2

    r_outer = size * TR_OUTER
    r_zodiac = size * TR_ZODIAC
    r_transit = size * TR_TRANSIT
    r_natal = size * TR_NATAL
    r_aspects = size * TR_ASPECTS

    use_symbols = _is_symbol_mode(label_mode)
    sign_font_size = SIGN_FONT_SIZES.get(label_mode, 10)
    planet_font_size = PLANET_FONT_SIZES.get(label_mode, 9)

    # Палитры с учётом переопределений из профиля
    final_planet_colors = _merge_colors(PLANET_COLORS, planet_colors)
    final_aspect_colors = _merge_colors(ASPECT_COLORS, aspect_colors)

    svg_parts = []

    svg_parts.append(_svg_header(size, 1.0, 0.0, 0.0))
    svg_parts.append(f'  <rect width="{size}" height="{size}" fill="white"/>\n')

    # 1. Круги
    svg_parts.append(_svg_circle(cx, cy, r_outer, stroke="black", stroke_width=2))
    svg_parts.append(_svg_circle(cx, cy, r_zodiac, stroke="black", stroke_width=1))
    svg_parts.append(_svg_circle(cx, cy, r_transit, stroke="black", stroke_width=0.5,
                                 stroke_dasharray="4,2"))
    svg_parts.append(_svg_circle(cx, cy, r_natal, stroke="black", stroke_width=0.5))
    svg_parts.append(_svg_circle(cx, cy, r_aspects, stroke="gray", stroke_width=0.5,
                                 stroke_dasharray="2,2"))

    # 2. Знаки зодиака
    for i, sign in enumerate(SIGNS):
        boundary_lon = i * 30.0
        x1, y1 = longitude_to_svg_coords(boundary_lon, r_zodiac, cx, cy)
        x2, y2 = longitude_to_svg_coords(boundary_lon, r_outer, cx, cy)
        svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="black", stroke_width=0.8))

        mid_lon = boundary_lon + 15.0
        x_text, y_text = longitude_to_svg_coords(mid_lon, (r_zodiac + r_outer) / 2, cx, cy)

        sign_label = _get_sign_label(sign, label_mode)
        svg_parts.append(_svg_text(
            x_text, y_text, sign_label,
            font_size=sign_font_size, fill="black", use_symbol_font=use_symbols
        ))

    # 3. Дома (из натальной карты, если включены)
    houses = natal_chart.get("houses", [])

    if houses and show_houses:
        for house in houses:
            cusp_lon = house.get("longitude")
            if cusp_lon is None:
                continue

            x1, y1 = longitude_to_svg_coords(cusp_lon, r_aspects, cx, cy)
            x2, y2 = longitude_to_svg_coords(cusp_lon, r_natal, cx, cy)

            lw = 1.5 if house.get("house") == 1 else 0.8
            svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="black", stroke_width=lw))

            house_number = house.get("house", 0)
            next_idx = house_number % len(houses)
            next_cusp_lon = houses[next_idx].get("longitude", cusp_lon)

            diff = (next_cusp_lon - cusp_lon) % 360
            mid_lon = (cusp_lon + diff / 2) % 360
            x_text, y_text = longitude_to_svg_coords(mid_lon, (r_aspects + r_natal) / 2, cx, cy)

            svg_parts.append(_svg_text(x_text, y_text, str(house_number),
                                       font_size=14, fill="gray"))

    # 3.5. Дома транзита (если переданы и дома включены)
    if transit_houses and show_houses:
        for house in transit_houses:
            cusp_lon = house.get("longitude")
            if cusp_lon is None:
                continue

            x1, y1 = longitude_to_svg_coords(cusp_lon, r_transit, cx, cy)
            x2, y2 = longitude_to_svg_coords(cusp_lon, r_zodiac, cx, cy)

            lw = 1.5 if house.get("house") == 1 else 0.8
            svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="#2A9D8F", stroke_width=lw))

            house_number = house.get("house", 0)
            next_idx = house_number % len(transit_houses)
            next_cusp_lon = transit_houses[next_idx].get("longitude", cusp_lon)

            diff = (next_cusp_lon - cusp_lon) % 360
            mid_lon = (cusp_lon + diff / 2) % 360
            x_text, y_text = longitude_to_svg_coords(mid_lon, (r_transit + r_zodiac) / 2, cx, cy)

            svg_parts.append(_svg_text(x_text, y_text, str(house_number),
                                       font_size=12, fill="#2A9D8F"))

    # 4. Натальные планеты (внутренний круг, исправленное смещение)
    natal_planets = natal_chart.get("planets", [])
    natal_positions = {}

    sorted_natal = sorted(natal_planets, key=lambda p: p.get("longitude", 0))
    used_positions_natal = []

    for planet in sorted_natal:
        lon = planet.get("longitude")
        if lon is None:
            continue

        planet_name = planet.get("name", "?")

        radius = _resolve_planet_radius(lon, size, r_natal, used_positions_natal)
        used_positions_natal.append((lon, radius))

        x, y = longitude_to_svg_coords(lon, radius, cx, cy)
        natal_positions[planet_name] = (x, y)

        is_retrograde = planet.get("retrograde", False)
        base_color = final_planet_colors.get(planet_name, COLOR_NATAL)
        dot_stroke = "#D62828" if is_retrograde else "none"
        dot_stroke_width = 1.5 if is_retrograde else 0

        planet_ru = get_planet_name_ru(planet_name)
        sign_ru = get_sign_name_ru(planet.get("sign", ""))

        svg_parts.append(
            f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{planet_dot_size}" fill="{base_color}" '
            f'stroke="{dot_stroke}" stroke-width="{dot_stroke_width}" '
            f'class="natal-planet" data-planet="{planet_ru}" '
            f'data-lon="{lon:.6f}" data-speed="0" '
            f'data-sign="{sign_ru}"/>\n'
        )

        planet_label = _get_planet_label(planet_name, label_mode)
        if is_retrograde:
            planet_label += " R"

        x_label, y_label = longitude_to_svg_coords(lon, radius + size * 0.025, cx, cy)
        text_color = "black" if base_color in ("#000000", "#660000") else base_color
        svg_parts.append(_svg_text(
            x_label, y_label, planet_label,
            font_size=planet_font_size, fill=text_color, use_symbol_font=use_symbols
        ))

    # 5. Транзитные планеты (внешний круг, исправленное смещение)
    transit_positions = {}

    sorted_transit = sorted(transit_planets, key=lambda p: p.get("longitude", 0))
    used_positions_transit = []

    for planet in sorted_transit:
        lon = planet.get("longitude")
        if lon is None:
            continue

        planet_name = planet.get("name", "?")

        radius = _resolve_planet_radius(lon, size, r_transit, used_positions_transit)
        used_positions_transit.append((lon, radius))

        x, y = longitude_to_svg_coords(lon, radius, cx, cy)
        transit_positions[planet_name] = (x, y)

        is_retrograde = planet.get("retrograde", False)
        base_color = final_planet_colors.get(planet_name, COLOR_TRANSIT)
        dot_stroke = "#D62828" if is_retrograde else "none"
        dot_stroke_width = 1.5 if is_retrograde else 0

        planet_ru = get_planet_name_ru(planet_name)
        sign_ru = get_sign_name_ru(planet.get("sign", ""))
        speed_lon = planet.get("speed_longitude", 0)

        svg_parts.append(
            f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{planet_dot_size}" fill="{base_color}" '
            f'stroke="{dot_stroke}" stroke-width="{dot_stroke_width}" '
            f'class="transit-planet" data-planet="{planet_ru}" '
            f'data-lon="{lon:.6f}" data-speed="{speed_lon:.6f}" '
            f'data-sign="{sign_ru}"/>\n'
        )

        planet_label = _get_planet_label(planet_name, label_mode)
        if is_retrograde:
            planet_label += " R"

        x_label, y_label = longitude_to_svg_coords(lon, radius + size * 0.025, cx, cy)
        text_color = "black" if base_color in ("#000000", "#660000") else base_color
        svg_parts.append(_svg_text(
            x_label, y_label, planet_label,
            font_size=planet_font_size, fill=text_color, use_symbol_font=use_symbols
        ))

    # 6. Натальные аспекты (внутри внутреннего круга)
    if show_aspects:
        natal_aspects = natal_chart.get("aspects", [])

        for aspect in natal_aspects:
            point_a = aspect.get("point_a")
            point_b = aspect.get("point_b")
            aspect_name = aspect.get("aspect")

            if point_a in natal_positions and point_b in natal_positions:
                x1, y1 = natal_positions[point_a]
                x2, y2 = natal_positions[point_b]

                color = final_aspect_colors.get(aspect_name, "gray")
                svg_parts.append(_svg_line(x1, y1, x2, y2, stroke=color,
                                           stroke_width=0.8, opacity=0.6))

    # 7. Транзитные аспекты (между кругами, пунктиром)
    if show_aspects:
        for aspect in transit_aspects:
            transit_planet_name = aspect.get("transit_planet")
            natal_point_name = aspect.get("natal_point")
            aspect_name = aspect.get("aspect")

            if transit_planet_name in transit_positions and natal_point_name in natal_positions:
                x1, y1 = transit_positions[transit_planet_name]
                x2, y2 = natal_positions[natal_point_name]

                color = final_aspect_colors.get(aspect_name, "gray")
                svg_parts.append(_svg_line(x1, y1, x2, y2, stroke=color,
                                           stroke_width=1, stroke_dasharray="4,3",
                                           opacity=0.8))

    # 8. ASC и MC (из натальной карты)
    additional_points = natal_chart.get("additional_points", [])

    for point in additional_points:
        point_name = point.get("name")
        lon = point.get("longitude")

        if point_name is None or lon is None:
            continue

        if point_name == "ASC":
            x1, y1 = longitude_to_svg_coords(lon, r_natal, cx, cy)
            x2, y2 = longitude_to_svg_coords(lon, r_outer, cx, cy)
            svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="red", stroke_width=2))

            x_text, y_text = longitude_to_svg_coords(lon, r_outer + size * 0.035, cx, cy)
            svg_parts.append(_svg_text(x_text, y_text, "ASC",
                                       font_size=16, fill="red", weight="bold"))

        elif point_name == "MC":
            x1, y1 = longitude_to_svg_coords(lon, r_natal, cx, cy)
            x2, y2 = longitude_to_svg_coords(lon, r_outer, cx, cy)
            svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="blue", stroke_width=2))

            x_text, y_text = longitude_to_svg_coords(lon, r_outer + size * 0.035, cx, cy)
            svg_parts.append(_svg_text(x_text, y_text, "MC",
                                       font_size=16, fill="blue", weight="bold"))

    # 8.5. Углы транзита (если переданы)
    if transit_additional_points:
        for point in transit_additional_points:
            point_name = point.get("name")
            lon = point.get("longitude")

            if point_name is None or lon is None:
                continue

            if point_name == "ASC":
                x1, y1 = longitude_to_svg_coords(lon, r_transit, cx, cy)
                x2, y2 = longitude_to_svg_coords(lon, r_outer, cx, cy)
                svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="#E76F51", stroke_width=2))

                x_text, y_text = longitude_to_svg_coords(lon, r_outer + size * 0.035, cx, cy)
                svg_parts.append(_svg_text(x_text, y_text, "Тр. ASC",
                                           font_size=11, fill="#E76F51", weight="bold"))

            elif point_name == "MC":
                x1, y1 = longitude_to_svg_coords(lon, r_transit, cx, cy)
                x2, y2 = longitude_to_svg_coords(lon, r_outer, cx, cy)
                svg_parts.append(_svg_line(x1, y1, x2, y2, stroke="#E9C46A", stroke_width=2))

                x_text, y_text = longitude_to_svg_coords(lon, r_outer + size * 0.035, cx, cy)
                svg_parts.append(_svg_text(x_text, y_text, "Тр. MC",
                                           font_size=11, fill="#E9C46A", weight="bold"))

    # Заголовок
    chart_name = natal_chart.get("birth", {}).get("name", "Транзитная карта")
    title = f"Транзитная карта: {chart_name}"
    svg_parts.append(
        f'  <text x="{cx}" y="{size * 0.03}" '
        f'font-family="Segoe UI, Arial, sans-serif" font-size="14" '
        f'fill="black" text-anchor="middle" font-weight="bold">{escape(title)}</text>\n'
    )

    svg_parts.append(_svg_footer())

    return ''.join(svg_parts)