from .constants import SIGNS


def normalize_longitude(value):
    """
    Приводит долготу к диапазону [0, 360).
    """
    return float(value % 360.0)


def sign_from_longitude(longitude):
    """
    Возвращает знак зодиака и градус внутри знака.
    """
    longitude = normalize_longitude(longitude)
    sign_index = int(longitude // 30.0)
    degree_in_sign = longitude - sign_index * 30.0

    return SIGNS[sign_index], float(degree_in_sign)


def angle_between(longitude_a, longitude_b):
    """
    Возвращает минимальный угол между двумя точками зодиака.
    """
    diff = abs(normalize_longitude(longitude_a) - normalize_longitude(longitude_b))
    diff = diff % 360.0

    if diff > 180.0:
        diff = 360.0 - diff

    return float(diff)


def house_for_longitude(cusp_longitudes, longitude):
    """
    Определяет номер дома по долготе и списку куспидов.
    """
    if not cusp_longitudes:
        return None

    longitude = normalize_longitude(longitude)
    house_count = len(cusp_longitudes)

    for index in range(house_count):
        start = normalize_longitude(cusp_longitudes[index])
        end = normalize_longitude(cusp_longitudes[(index + 1) % house_count])

        if start == end:
            continue

        if start < end:
            if start <= longitude < end:
                return index + 1
        else:
            if longitude >= start or longitude < end:
                return index + 1

    return None