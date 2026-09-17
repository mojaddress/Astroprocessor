"""
Проверочный скрипт для обновлённого модуля отображения карты.

Создаёт три варианта карты для проверки:
1. Только символы (по умолчанию, увеличенные)
2. Символы + слова
3. Только слова
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

# Вариант 1: только символы (по умолчанию)
print("Генерируем вариант 1: только символы (по умолчанию)...")
svg1 = render_natal_chart_svg(natal)
with open("test_v3_symbols.svg", "w", encoding="utf-8") as f:
    f.write(svg1)

# Вариант 2: символы + слова
print("Генерируем вариант 2: символы + слова...")
svg2 = render_natal_chart_svg(natal, label_mode="both")
with open("test_v3_both.svg", "w", encoding="utf-8") as f:
    f.write(svg2)

# Вариант 3: только слова
print("Генерируем вариант 3: только слова...")
svg3 = render_natal_chart_svg(natal, label_mode="words")
with open("test_v3_words.svg", "w", encoding="utf-8") as f:
    f.write(svg3)

print("")
print("Готово! Созданы файлы:")
print("  test_v3_symbols.svg  - только символы (по умолчанию, увеличенные)")
print("  test_v3_both.svg     - символы + слова")
print("  test_v3_words.svg    - только слова")
print("")
print("Откройте каждый файл в браузере (двойной клик) для просмотра.")