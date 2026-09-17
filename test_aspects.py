from astro_core.aspects import calculate_aspects


def test_square_aspect():
    points = [
        {"name": "A", "longitude": 0.0},
        {"name": "B", "longitude": 90.5},
    ]

    settings = {
        "enabled_aspects": ["square"],
        "orbs": {"square": 1.0},
    }

    aspects = calculate_aspects(points, settings)

    assert len(aspects) == 1
    assert aspects[0]["aspect"] == "square"
    assert aspects[0]["orb"] == 0.5


def test_no_aspect_if_orb_too_small():
    points = [
        {"name": "A", "longitude": 0.0},
        {"name": "B", "longitude": 95.0},
    ]

    settings = {
        "enabled_aspects": ["square"],
        "orbs": {"square": 1.0},
    }

    aspects = calculate_aspects(points, settings)

    assert len(aspects) == 0


def test_best_aspect_selected():
    points = [
        {"name": "A", "longitude": 0.0},
        {"name": "B", "longitude": 120.2},
    ]

    settings = {
        "enabled_aspects": ["trine", "square"],
        "orbs": {
            "trine": 2.0,
            "square": 2.0,
        },
    }

    aspects = calculate_aspects(points, settings)

    assert len(aspects) == 1
    assert aspects[0]["aspect"] == "trine"