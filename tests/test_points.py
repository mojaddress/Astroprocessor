from astro_core.points import is_day_chart, part_of_fortune


def test_is_day_chart():
    assert is_day_chart(90.0, 0.0) is True
    assert is_day_chart(270.0, 0.0) is False


def test_part_of_fortune_day():
    result = part_of_fortune(0.0, 10.0, 100.0, True)

    assert abs(result - 90.0) < 1e-9


def test_part_of_fortune_night():
    result = part_of_fortune(0.0, 10.0, 100.0, False)

    assert abs(result - 270.0) < 1e-9


def test_part_of_fortune_normalization():
    result = part_of_fortune(350.0, 10.0, 20.0, True)

    assert 0.0 <= result < 360.0