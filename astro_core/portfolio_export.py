"""
Экспорт портфеля карт в один самодостаточный HTML-файл (итерация 31).
Без внешних зависимостей: изображение встраивается base64, стили — inline CSS.
"""
from datetime import datetime
from html import escape
from typing import Dict, Optional

from .constants import get_planet_name_ru, get_sign_name_ru
from .interpretations import ASPECT_INFO, DISCLAIMER

CSS = """
body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #222; }
h1 { font-size: 24px; } h2 { font-size: 19px; margin-top: 28px;
     border-bottom: 2px solid #7a5fb0; padding-bottom: 4px; }
table { border-collapse: collapse; margin: 8px 0 16px 0; width: 100%; }
th, td { border: 1px solid #bbb; padding: 4px 8px; font-size: 13px; text-align: left; }
th { background: #efeaf7; }
pre { background: #f6f6f6; border: 1px solid #ddd; padding: 10px;
      white-space: pre-wrap; font-size: 13px; }
img { max-width: 720px; border: 1px solid #999; }
.meta { color: #666; font-size: 12px; }
.disc { color: #8a4b4b; font-size: 12px; margin-top: 24px; }
"""


def _table(headers, rows) -> str:
    out = ["<table><tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr>"]
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>")
    out.append("</table>")
    return "".join(out)


def _planet_rows(chart: Dict):
    rows = []
    objs = list(chart.get("planets", [])) + list(chart.get("additional_points", []))
    for p in objs:
        lon = p.get("longitude", 0.0) or 0.0
        deg = p.get("degree_in_sign")
        if deg is None:
            deg = lon % 30.0
        rows.append([
            get_planet_name_ru(p.get("name", "")),
            f"{int(round(deg)) % 30}°",
            f"{lon:.2f}",
            get_sign_name_ru(p.get("sign", "")),
            str(p.get("house") or "—"),
            "R" if p.get("retrograde") else "",
        ])
    return rows


def _aspect_rows(aspects) -> list:
    rows = []
    for a in aspects or []:
        info = ASPECT_INFO.get(a.get("aspect", ""), {})
        rows.append([
            get_planet_name_ru(a.get("point_a", "")),
            get_planet_name_ru(a.get("point_b", "")),
            info.get("name", a.get("aspect", "")),
            f"{abs(a.get('orb', 0.0)):.2f}",
            f"{a.get('score', 0):+d}",
        ])
    return rows


def build_portfolio_html(*, person: str, birth_line: str,
                         image_b64: Optional[str] = None,
                         image_caption: str = "Вид карты на момент экспорта",
                         natal_chart: Optional[Dict] = None,
                         transits_text: Optional[str] = None,
                         directions: Optional[Dict] = None,
                         directions_date: Optional[str] = None,
                         solar_chart: Optional[Dict] = None,
                         solar_year: Optional[int] = None,
                         synastry: Optional[Dict] = None,
                         analysis_text: Optional[str] = None) -> str:
    """Собирает все переданные разделы в один HTML-документ."""
    parts = ["<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'>",
             f"<title>Астрологический портфель: {escape(person)}</title>",
             f"<style>{CSS}</style></head><body>"]
    parts.append(f"<h1>Астрологический портфель: {escape(person)}</h1>")
    parts.append(f"<p class='meta'>Рождение: {escape(birth_line)}<br>"
                 f"Сформировано: {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
                 "Astro Processor · файл самодостаточен (изображение встроено, "
                 "внешних ссылок нет)</p>")
    if image_b64:
        parts.append(f"<h2>Карта</h2><img src='data:image/png;base64,{image_b64}' "
                     f"alt='карта'><p class='meta'>{escape(image_caption)}</p>")
    if natal_chart:
        parts.append("<h2>Натальная карта: планеты и точки</h2>")
        parts.append(_table(["Объект", "Градусы", "Долгота", "Знак", "Дом", "Ретро"],
                            _planet_rows(natal_chart)))
        parts.append("<h2>Натальные аспекты</h2>")
        parts.append(_table(["Точка A", "Точка B", "Аспект", "Орб", "Баллы"],
                            _aspect_rows(natal_chart.get("aspects", []))))
    if transits_text:
        parts.append("<h2>Транзиты (сводка)</h2>")
        parts.append(f"<pre>{escape(transits_text)}</pre>")
    if directions:
        arc = directions.get("arc", 0.0)
        deg = int(arc)
        mins = int(round((arc - deg) * 60))
        head = f"<h2>Дирекции (солнечная дуга)"
        if directions_date:
            head += f" на {escape(str(directions_date))}"
        head += f" — дуга {deg}°{mins:02d}'</h2>"
        parts.append(head)
        parts.append(_table(["Дир. планета", "Долгота", "Знак", "° в знаке"],
                            [[get_planet_name_ru(p.get("name", "")),
                              f"{p.get('longitude', 0.0):.2f}",
                              get_sign_name_ru(p.get("sign", "")),
                              f"{int(round(p.get('degree_in_sign') or 0.0)) % 30}°"]
                             for p in directions.get("planets", [])]))
        parts.append(_table(["Дир. планета", "Натальная точка", "Аспект", "Орб", "Баллы"],
                            [[get_planet_name_ru(a.get("dir_planet", "")),
                              get_planet_name_ru(a.get("natal_point", "")),
                              ASPECT_INFO.get(a.get("aspect", ""), {}).get(
                                  "name", a.get("aspect", "")),
                              f"{abs(a.get('orb', 0.0)):.2f}",
                              f"{a.get('score', 0):+d}"]
                             for a in directions.get("aspects", [])]))
    if solar_chart is not None and solar_year:
        b = solar_chart.get("birth", {})
        parts.append(f"<h2>Соляр {int(solar_year)}: момент {escape(str(b.get('date', '')))} "
                     f"{escape(str(b.get('time', '')))} UTC</h2>")
        parts.append(_table(["Объект", "Градусы", "Долгота", "Знак", "Дом", "Ретро"],
                            _planet_rows(solar_chart)))
        parts.append(_table(["Точка A", "Точка B", "Аспект", "Орб", "Баллы"],
                            _aspect_rows(solar_chart.get("aspects", []))))
    if synastry:
        parts.append(f"<h2>Синастрия: {escape(str(synastry.get('name_a', '')))} × "
                     f"{escape(str(synastry.get('name_b', '')))}</h2>")
        rows = []
        for a in synastry.get("aspects", []):
            info = ASPECT_INFO.get(a.get("aspect", ""), {})
            rows.append([
                f"{get_planet_name_ru(a.get('point_a', ''))} ({a.get('point_a_chart', '')})",
                f"{get_planet_name_ru(a.get('point_b', ''))} ({a.get('point_b_chart', '')})",
                info.get("name", a.get("aspect", "")),
                f"{abs(a.get('orb', 0.0)):.2f}",
                f"{a.get('score', 0):+d}",
            ])
        parts.append(_table(["Человек A", "Человек B", "Аспект", "Орб", "Баллы"], rows))
    if analysis_text:
        parts.append("<h2>Анализ (сводка)</h2>")
        parts.append(f"<pre>{escape(analysis_text)}</pre>")
    parts.append(f"<p class='disc'>{escape(DISCLAIMER)}</p>")
    parts.append("</body></html>")
    return "".join(parts)
