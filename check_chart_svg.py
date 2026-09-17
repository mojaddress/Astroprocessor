"""
Проверочный скрипт для модуля графического отображения карты в SVG.

Рисует натальную карту и сохраняет её в файл SVG.
SVG можно открыть в любом браузере.
"""

from astro_core.chart import build_natal_chart
from astro_core.chart_svg import render_natal_chart_svg


# Данные натальной карты
birth = {
    "name": "Demo",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
}

natal_settings = {
    "include_chiron": False,
    "include_nodes": False,
}

print("Строим натальную карту...")
natal = build_natal_chart(birth, natal_settings)

print("Генерируем SVG...")
svg_content = render_natal_chart_svg(natal, show_aspects=True)

output_file = "test_chart.svg"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"Карта сохранена в файл: {output_file}")
print("Откройте этот файл в браузере (двойной клик) для просмотра.")