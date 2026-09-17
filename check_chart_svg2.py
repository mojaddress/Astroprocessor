"""
Проверочный скрипт для обновлённого модуля отображения карты.

Создаёт четыре варианта карты для проверки:
1. Обычная карта со словами
2. Карта только с символами
3. Карта с символами и словами
4. Увеличенная карта (зум 1.5)
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

# Вариант 1: слова (по умолчанию)
print("Генерируем вариант 1: слова...")
svg1 = render_natal_chart_svg(natal, label_mode="words")
with open("test_chart_words.svg", "w", encoding="utf-8") as f:
    f.write(svg1)

# Вариант 2: только символы
print("Генерируем вариант 2: символы...")
svg2 = render_natal_chart_svg(natal, label_mode="symbols")
with open("test_chart_symbols.svg", "w", encoding="utf-8") as f:
    f.write(svg2)

# Вариант 3: символы + слова
print("Генерируем вариант 3: символы + слова...")
svg3 = render_natal_chart_svg(natal, label_mode="both")
with open("test_chart_both.svg", "w", encoding="utf-8") as f:
    f.write(svg3)

# Вариант 4: увеличенная карта
print("Генерируем вариант 4: зум 1.5...")
svg4 = render_natal_chart_svg(natal, label_mode="symbols", zoom=1.5)
with open("test_chart_zoom.svg", "w", encoding="utf-8") as f:
    f.write(svg4)

print("")
print("Готово! Созданы файлы:")
print("  test_chart_words.svg    - подписи словами")
print("  test_chart_symbols.svg  - подписи символами")
print("  test_chart_both.svg     - символы + слова")
print("  test_chart_zoom.svg     - увеличенная карта (зум 1.5)")
print("")
print("Откройте каждый файл в браузере (двойной клик) для просмотра.")