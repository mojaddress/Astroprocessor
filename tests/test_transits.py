"""Тесты транзитов (итерация 22): фейковые карты, без эфемерид."""

from datetime import date

from astro_core.transits_daily import scan_periods, summarize_transits, transit_aspects


def _chart(name, planets):
    return {"birth": {"name": name},
            "planets": [{"name": n, "longitude": lon} for n, lon in planets]}


NATAL = _chart("Анна", [("Sun", 100.0), ("Moon", 200.0), ("Mars", 300.0)])


def _sky(shift):
    return _chart("небо", [("Sun", 100.0 + shift),
                           ("Moon", 200.0 + shift),
                           ("Mars", 300.0 + shift)])


def test_transit_cross_only():
    aspects = transit_aspects(NATAL, _sky(0.0))
    assert len(aspects) == 3
    assert all(a["aspect"] == "conjunction" for a in aspects)
    names = {a["transit_planet"] for a in aspects}
    assert names == {"Sun", "Moon", "Mars"}


def test_transit_orb_and_score():
    aspects = transit_aspects(NATAL, _sky(2.0))
    conj = [a for a in aspects if a["transit_planet"] == "Sun"]
    assert conj and abs(conj[0]["orb"] - 2.0) < 1e-6
    assert conj[0]["score"] > 0


def test_transit_respects_orb_limit():
    """Сдвиг 9°: орб конъюнкции 9° превышает лимит 8° — конъюнкций нет."""
    aspects = transit_aspects(NATAL, _sky(9.0))
    # Ни одной конъюнкции (орб 9° > лимит 8°)
    assert not any(a["aspect"] == "conjunction" for a in aspects)
    # Но другие аспекты (квадраты между разными планетами) могут присутствовать
    # — они не нарушают лимит конъюнкции


def test_scan_periods_groups_days():
    def get_sky(d):
        delta = (d - date(2025, 1, 3)).days
        return _sky(abs(delta) * 1.0)
    periods = scan_periods(NATAL, date(2025, 1, 1), 7, get_sky)
    conj_sun = [p for p in periods
                if p["transit_planet"] == "Sun" and p["aspect"] == "conjunction"]
    assert conj_sun
    p = conj_sun[0]
    assert p["start"] == date(2025, 1, 1)
    assert p["end"] == date(2025, 1, 7)
    assert p["exact_date"] == date(2025, 1, 3)


def test_summarize_contains_sections():
    aspects = transit_aspects(NATAL, _sky(1.0))
    text = summarize_transits(NATAL, aspects, date(2025, 1, 3))
    assert "Поддержка сегодня:" in text
    assert "Напряжение сегодня:" in text
    assert "Анна" in text
