from astro_core.utils import normalize_longitude, sign_from_longitude, angle_between


def test_normalize_longitude():
    assert normalize_longitude(0.0) == 0.0
    assert normalize_longitude(360.0) == 0.0
    assert normalize_longitude(361.5) == 1.5
    assert normalize_longitude(-1.0) == 359.0


def test_sign_from_longitude():
    sign, degree = sign_from_longitude(0.0)
    assert sign == "Aries"
    assert degree == 0.0

    sign, degree = sign_from_longitude(35.0)
    assert sign == "Taurus"
    assert degree == 5.0

    sign, degree = sign_from_longitude(359.9)
    assert sign == "Pisces"
    assert abs(degree - 29.9) < 1e-9


def test_angle_between():
    assert angle_between(0.0, 90.0) == 90.0
    assert angle_between(0.0, 270.0) == 90.0
    assert angle_between(0.0, 180.0) == 180.0
    assert abs(angle_between(0.0, 359.5) - 0.5) < 1e-9