"""
Проверочный скрипт для модуля прогрессий.

Рассчитывает вторичные прогрессии и прогрессии солнечной дуги
для демонстрационной карты и выводит результаты.
"""

from astro_core.chart import build_natal_chart
from astro_core.progressions import (
    calculate_secondary_progressions,
    calculate_solar_arc_progressions,
    find_progression_aspects,
)

# Данные натальной карты
birth = {
    "name": "Demo",
    "date": "1990-05-15",
    "time": "14:30",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3,
}

settings = {
    "include_chiron": False,
    "include_nodes": False,
}

# Дата прогрессии (30 лет)
progression_date = "2020-05-15"

print("=" * 60)
print("Натальная карта")
print("=" * 60)

natal = build_natal_chart(birth, settings)
natal_sun = next((p for p in natal["planets"] if p["name"] == "Sun"), None)
print(f"Натальное Солнце: {natal_sun['longitude']:.2f}° ({natal_sun['sign']})")

print("\n" + "=" * 60)
print(f"Вторичные прогрессии на {progression_date}")
print("=" * 60)

secondary = calculate_secondary_progressions(birth, progression_date, settings)
print(f"Возраст: {secondary['age_years']} лет")

progressed_sun = next((p for p in secondary["planets"] if p["name"] == "Sun"), None)
print(f"Прогрессивное Солнце: {progressed_sun['longitude']:.2f}° ({progressed_sun['sign']})")

print("\nПрогрессивные планеты:")
for obj in secondary["planets"]:
    print(f"  {obj['name']:10s} {obj['longitude']:8.2f}° {obj['sign']}")

print("\n" + "=" * 60)
print(f"Прогрессии солнечной дуги на {progression_date}")
print("=" * 60)

solar_arc = calculate_solar_arc_progressions(birth, progression_date, settings)
print(f"Солнечная дуга: {solar_arc['solar_arc']:.2f}°")

print("\nПрогрессивные планеты солнечной дуги:")
for obj in solar_arc["planets"]:
    print(f"  {obj['name']:10s} {obj['longitude']:8.2f}° {obj['sign']}")

print("\n" + "=" * 60)
print("Аспекты прогрессий к натальным точкам")
print("=" * 60)

aspects = find_progression_aspects(natal["objects"], secondary["objects"], settings)
print(f"Найдено аспектов: {len(aspects)}")

print("\nПервые 10 аспектов:")
for aspect in aspects[:10]:
    print(
        f"  {aspect['progressed_planet']:10s} {aspect['aspect']:12s} "
        f"{aspect['natal_point']:10s} (орб {aspect['orb']:.2f}°)"
    )

print("\nГотово!")