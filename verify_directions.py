"""Перекрёстная проверка дирекций: цепочка значений для сверки с эфемеридами."""
from datetime import date, timedelta

from astro_core.chart import build_natal_chart
from astro_core.directions import (
    _progressive_sun_longitude, _sun_longitude, calculate_directions, solar_arc,
)

BIRTH = {
    "name": "Сергей",
    "date": "1971-03-17",
    "time": "11:30",
    "latitude": 55.7887,
    "longitude": 49.1221,
    "utc_offset_hours": 3.0,
}
NATAL_DATE = date(1971, 3, 17)
TARGET = date(2026, 10, 18)

natal = build_natal_chart(BIRTH, {})
arc = solar_arc(natal, TARGET)
prog_date = NATAL_DATE + timedelta(days=55)
nat_sun = _sun_longitude(natal)
prog_sun = _progressive_sun_longitude(NATAL_DATE, TARGET)
res = calculate_directions(natal, TARGET)
dsun = next(p for p in res["planets"] if p["name"] == "Sun")

deg = int(arc)
mins = int(round((arc - deg) * 60))
print(f"Возраст на {TARGET}: 55 лет -> прогрессивная дата {prog_date}")
print(f"Натальное Солнце: {nat_sun:.4f} deg")
print(f"Прогрессивное Солнце: {prog_sun:.4f} deg")
print(f"Дуга: {arc:.4f} deg = {deg} deg {mins:02d}'")
print(f"Дирекционное Солнце: {dsun['longitude']:.2f} deg, "
      f"{dsun['sign']}, {dsun['degree_in_sign']:.2f} in sign")
print("Топ-3 аспекта:", [(a['dir_planet'], a['natal_point'], a['aspect'],
                          round(a['orb'], 2)) for a in res['aspects'][:3]])
print("Сверка с UI: дуга 54 deg 03', дир. Солнце 50.15 Taurus 20.15")
