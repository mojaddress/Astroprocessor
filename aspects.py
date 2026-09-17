from .constants import ASPECT_DEFINITIONS
from .utils import angle_between


def calculate_aspects(objects, settings):
    """
    Рассчитывает аспекты между объектами карты.

    Каждый объект должен иметь:
        name
        longitude

    Параметры:
        objects: список объектов
        settings: настройки аспектов и орбов

    Возвращает:
        список аспектов
    """

    aspects = []

    enabled_aspects = set(settings.get("enabled_aspects", []))
    orbs = settings.get("orbs", {})

    aspect_definitions = [
        aspect
        for aspect in ASPECT_DEFINITIONS
        if aspect["name"] in enabled_aspects
    ]

    if not aspect_definitions:
        return aspects

    for i in range(len(objects)):
        point_a = objects[i]

        if "longitude" not in point_a or "name" not in point_a:
            continue

        for j in range(i + 1, len(objects)):
            point_b = objects[j]

            if "longitude" not in point_b or "name" not in point_b:
                continue

            angle = angle_between(point_a["longitude"], point_b["longitude"])

            best_aspect = None

            for aspect_definition in aspect_definitions:
                aspect_name = aspect_definition["name"]
                exact_angle = float(aspect_definition["angle"])

                max_orb = float(orbs.get(aspect_name, 0.0))
                if max_orb <= 0.0:
                    continue

                orb = abs(angle - exact_angle)

                if orb <= max_orb:
                    strength = 1.0 - (orb / max_orb)

                    candidate = {
                        "point_a": point_a["name"],
                        "point_b": point_b["name"],
                        "aspect": aspect_name,
                        "angle": round(angle, 6),
                        "exact_angle": exact_angle,
                        "orb": round(orb, 6),
                        "max_orb": max_orb,
                        "strength": round(max(0.0, min(1.0, strength)), 6),
                    }

                    if best_aspect is None or candidate["orb"] < best_aspect["orb"]:
                        best_aspect = candidate

            if best_aspect is not None:
                aspects.append(best_aspect)

    return aspects