"""Итерация 31: экспорт портфеля в HTML."""
from astro_core.chart import build_natal_chart
from astro_core.portfolio_export import build_portfolio_html

BIRTH = {
    "name": "Тест",
    "date": "1990-05-15",
    "time": "12:00",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "utc_offset_hours": 3.0,
}


def test_html_sections_and_no_image():
    natal = build_natal_chart(BIRTH, {})
    html = build_portfolio_html(
        person="Тест", birth_line="1990-05-15 12:00",
        natal_chart=natal, transits_text="Транзитный текст",
        directions={"arc": 30.5, "planets": natal["planets"], "aspects": []},
        solar_chart=natal, solar_year=2026,
        analysis_text="Анализ")
    assert "<html" in html
    assert "Тест" in html
    assert "Дирекции" in html
    assert "Соляр 2026" in html
    assert "Транзитный текст" in html
    assert "data:image/png" not in html


def test_html_image_and_escaping():
    natal = build_natal_chart(BIRTH, {})
    html = build_portfolio_html(person="<b>X</b>", birth_line="b",
                                image_b64="QUJD", natal_chart=natal)
    assert "data:image/png;base64,QUJD" in html
    assert "<b>X</b>" not in html


def test_degrees_column_present():
    natal = build_natal_chart(BIRTH, {})
    html = build_portfolio_html(person="Т", birth_line="b", natal_chart=natal)
    assert "Градусы" in html
    assert "°</td>" in html
