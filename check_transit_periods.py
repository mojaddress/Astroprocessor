from astro_core.chart import build_natal_chart
from astro_core.transits import find_transit_periods

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

# Ищем периоды активности транзитов за короткий период
start_date = "1990-05-14"
end_date = "1990-05-16"

print(f"Searching for transit periods: {start_date} to {end_date}")
print("This may take a few seconds...\n")

periods = find_transit_periods(
    natal["objects"],
    start_date,
    end_date,
)

print(f"Periods found: {len(periods)}")

if periods:
    print("\nFirst 5 periods:")
    for period in periods[:5]:
        print(
            f"  {period['transit_planet']} {period['aspect']} {period['natal_point']} ({period['direction']})"
        )
        print(f"    Start: {period['start_datetime']}")
        print(f"    Exact: {period['exact_datetime']}")
        print(f"    End:   {period['end_datetime']}")
        print(f"    Orb:   {period['orb']}")
        print()
else:
    print("No periods found")