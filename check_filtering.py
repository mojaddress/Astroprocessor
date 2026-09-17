from astro_core.chart import build_natal_chart
from astro_core.transits import find_transit_events, find_transit_periods

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

# Строим натальную карту
natal = build_natal_chart(birth, natal_settings)

# Период для поиска
start_date = "1990-05-14"
end_date = "1990-05-16"

print("=" * 60)
print("Тест 1: Все транзиты (без фильтрации)")
print("=" * 60)

events_all = find_transit_events(natal["objects"], start_date, end_date)
print(f"Всего событий: {len(events_all)}")

print("\n" + "=" * 60)
print("Тест 2: Только Солнце (фильтрация по планетам)")
print("=" * 60)

events_sun = find_transit_events(
    natal["objects"], start_date, end_date,
    filter_planets=["Sun"]
)
print(f"Событий с Солнцем: {len(events_sun)}")
for event in events_sun[:5]:
    print(f"  {event['transit_planet']} {event['aspect']} {event['natal_point']}")

print("\n" + "=" * 60)
print("Тест 3: Только соединения (фильтрация по аспектам)")
print("=" * 60)

events_conjunction = find_transit_events(
    natal["objects"], start_date, end_date,
    filter_aspects=["conjunction"]
)
print(f"Событий с соединением: {len(events_conjunction)}")
for event in events_conjunction[:5]:
    print(f"  {event['transit_planet']} {event['aspect']} {event['natal_point']}")

print("\n" + "=" * 60)
print("Тест 4: Только Солнце и только соединения")
print("=" * 60)

events_sun_conjunction = find_transit_events(
    natal["objects"], start_date, end_date,
    filter_planets=["Sun"],
    filter_aspects=["conjunction"]
)
print(f"Событий: {len(events_sun_conjunction)}")
for event in events_sun_conjunction:
    print(f"  {event['transit_planet']} {event['aspect']} {event['natal_point']}")

print("\n" + "=" * 60)
print("Тест 5: Периоды активности с фильтрацией")
print("=" * 60)

periods = find_transit_periods(
    natal["objects"], start_date, end_date,
    filter_planets=["Sun"],
    filter_aspects=["conjunction"]
)
print(f"Периодов: {len(periods)}")
for period in periods:
    print(f"  {period['transit_planet']} {period['aspect']} {period['natal_point']}")
    print(f"    Start: {period['start_datetime']}")
    print(f"    Exact: {period['exact_datetime']}")
    print(f"    End:   {period['end_datetime']}")