"""
Модуль интерактивного отображения карт с поддержкой Zet9-style тултипов.
"""
import uuid
from .chart_svg import render_natal_chart_svg, render_transit_chart_svg

# Стили для тултипа и контейнера карты.
# ВАЖНО: убрана фиксированная высота 85vh, чтобы контейнер не создавал
# лишнюю тёмную область и не обрезал элементы страницы.
_CSS_STYLES = """
<style>
.astro-chart-container {
    width: 100%;
    overflow: visible;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    background-color: white;
}
.astro-chart-container svg {
    max-width: 100%;
    cursor: grab;
}
.astro-tooltip {
    position: fixed;
    background-color: rgba(20, 20, 25, 0.95);
    color: #fff;
    padding: 10px 14px;
    border-radius: 6px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    pointer-events: none;
    z-index: 9999;
    box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    border: 1px solid #444;
    white-space: nowrap;
    display: none;
}
.astro-tooltip strong {
    color: #FFD700;
    display: block;
    font-size: 14px;
    margin-bottom: 2px;
    border-bottom: 1px solid #555;
    padding-bottom: 2px;
}
</style>
"""

# JavaScript для зума, панорамирования и тултипов
_INTERACTIVE_SCRIPT_TEMPLATE = """
<script>
document.addEventListener('DOMContentLoaded', function() {{
    var svg = document.getElementById('{svg_id}');
    if (!svg) return;

    var initialViewBox = {{ x: svg.viewBox.baseVal.x, y: svg.viewBox.baseVal.y, width: svg.viewBox.baseVal.width, height: svg.viewBox.baseVal.height }};
    var viewBox = {{ x: initialViewBox.x, y: initialViewBox.y, width: initialViewBox.width, height: initialViewBox.height }};

    function updateViewBox() {{
        svg.setAttribute('viewBox', viewBox.x + ' ' + viewBox.y + ' ' + viewBox.width + ' ' + viewBox.height);
    }}

    // --- Зум колесом мыши ---
    svg.addEventListener('wheel', function(e) {{
        e.preventDefault();
        var scaleFactor = e.deltaY > 0 ? 1.1 : 0.9;
        var rect = svg.getBoundingClientRect();
        var mouseX = (e.clientX - rect.left) / rect.width * viewBox.width + viewBox.x;
        var mouseY = (e.clientY - rect.top) / rect.height * viewBox.height + viewBox.y;
        var newWidth = viewBox.width * scaleFactor;
        var newHeight = viewBox.height * scaleFactor;
        if (newWidth < 50 || newWidth > 5000) return;
        viewBox.x = mouseX - (mouseX - viewBox.x) * scaleFactor;
        viewBox.y = mouseY - (mouseY - viewBox.y) * scaleFactor;
        viewBox.width = newWidth;
        viewBox.height = newHeight;
        updateViewBox();
    }}, {{ passive: false }});

    // --- Перетаскивание карты (панорамирование) ---
    var isDragging = false, lastX = 0, lastY = 0;
    svg.addEventListener('pointerdown', function(e) {{
        isDragging = true;
        lastX = e.clientX;
        lastY = e.clientY;
        svg.style.cursor = 'grabbing';
        svg.setPointerCapture(e.pointerId);
    }});
    svg.addEventListener('pointermove', function(e) {{
        if (!isDragging) return;
        var rect = svg.getBoundingClientRect();
        viewBox.x -= (e.clientX - lastX) / rect.width * viewBox.width;
        viewBox.y -= (e.clientY - lastY) / rect.height * viewBox.height;
        lastX = e.clientX;
        lastY = e.clientY;
        updateViewBox();
    }});
    svg.addEventListener('pointerup', function(e) {{ isDragging = false; svg.style.cursor = 'grab'; }});
    svg.addEventListener('pointerleave', function(e) {{ isDragging = false; svg.style.cursor = 'grab'; }});

    // --- Zet9-style Тултипы ---
    var tooltip = document.createElement('div');
    tooltip.className = 'astro-tooltip';
    document.body.appendChild(tooltip);
    var container = svg.parentElement;
    if (window.getComputedStyle(container).position === 'static') container.style.position = 'relative';

    svg.addEventListener('mousemove', function(e) {{
        var target = e.target;
        var planetName = target.getAttribute('data-planet');
        var lon = target.getAttribute('data-lon');
        var speed = target.getAttribute('data-speed');
        var signName = target.getAttribute('data-sign');

        if (planetName && lon) {{
            var lonF = parseFloat(lon);
            var deg = Math.floor(lonF % 30);
            var minF = (lonF % 30 - deg) * 60;
            var min = Math.floor(minF);

            var speedF = parseFloat(speed);
            var ret = speedF < 0 ? " (R)" : "";
            var speedStr = speedF >= 0 ? "+" + speedF.toFixed(3) : speedF.toFixed(3);

            tooltip.innerHTML = `<strong>${{planetName}}</strong>${{deg}}° ${{min}}' ${{signName}}<br>Скорость: ${{speedStr}}°/день ${{ret}}`;

            var rect = container.getBoundingClientRect();
            tooltip.style.left = (e.clientX - rect.left + 20) + 'px';
            tooltip.style.top = (e.clientY - rect.top + 20) + 'px';
            tooltip.style.display = 'block';
        }} else {{
            tooltip.style.display = 'none';
        }}
    }});
    svg.addEventListener('mouseleave', function() {{ tooltip.style.display = 'none'; }});
}});
</script>
"""


def _make_interactive_html(svg_content):
    """Оборачивает SVG в HTML с интерактивностью."""
    svg_id = f"astro-svg-{uuid.uuid4().hex[:8]}"
    svg_content = svg_content.replace('<svg ', f'<svg id="{svg_id}" ', 1)
    html = f"{_CSS_STYLES}<div class='astro-chart-container'>{svg_content}</div>"
    html += _INTERACTIVE_SCRIPT_TEMPLATE.format(svg_id=svg_id)
    return html


def render_interactive_chart(chart_data, size=800, show_aspects=True, label_mode="symbols"):
    """Генерирует интерактивную натальную карту."""
    svg_content = render_natal_chart_svg(
        chart_data, size=size, show_aspects=show_aspects, label_mode=label_mode
    )
    return _make_interactive_html(svg_content)


def render_interactive_transit_chart(natal_chart, transit_planets, transit_aspects,
                                     size=800, label_mode="symbols", show_aspects=True,
                                     transit_houses=None, transit_additional_points=None):
    """Генерирует интерактивную транзитную карту."""
    svg_content = render_transit_chart_svg(
        natal_chart, transit_planets, transit_aspects, size=size, label_mode=label_mode,
        show_aspects=show_aspects, transit_houses=transit_houses,
        transit_additional_points=transit_additional_points
    )
    return _make_interactive_html(svg_content)