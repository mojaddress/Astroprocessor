"""
Synastry Controller — расчёт совместимости двух натальных карт.

Считает аспекты между планетами двух карт, вычисляет числовую оценку.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from ..aspects import calculate_aspects


@dataclass
class SynastryResult:
    """Результат синастрии."""
    chart_a_name: str
    chart_b_name: str
    aspects: List[Dict]
    total_score: int
    max_possible_score: int
    compatibility_percentage: float


class SynastryController:
    """Контроллер для расчёта совместимости двух карт."""

    # Баллы за аспекты (упрощённая система)
    ASPECT_SCORES = {
        "conjunction": 10,
        "trine": 8,
        "sextile": 6,
        "square": -3,
        "opposition": -2,
    }

    def __init__(self):
        pass

    def calculate_synastry(
        self,
        chart_a: Dict,
        chart_b: Dict,
        orbs: Optional[Dict] = None
    ) -> SynastryResult:
        """
        Рассчитывает синастрию между двумя картами.

        Args:
            chart_a: результат build_natal_chart для первого человека
            chart_b: результат build_natal_chart для второго человека
            orbs: орбы аспектов (опционально)

        Returns:
            SynastryResult с аспектами и оценкой совместимости
        """
        objects_a = chart_a.get("planets", [])
        objects_b = chart_b.get("planets", [])

        # Объединяем объекты для расчёта аспектов
        combined_objects = objects_a + objects_b

        # Рассчитываем все аспекты
        if orbs is None:
            orbs = {
                "conjunction": 8.0,
                "opposition": 8.0,
                "square": 6.0,
                "trine": 6.0,
                "sextile": 4.0,
            }

        settings = {"enabled_aspects": list(orbs.keys()), "orbs": orbs}
        all_aspects = calculate_aspects(combined_objects, settings)

        # Фильтруем только аспекты между картами (не внутри одной карты)
        synastry_aspects = []
        names_a = {obj["name"] for obj in objects_a}
        names_b = {obj["name"] for obj in objects_b}

        for aspect in all_aspects:
            pa = aspect["point_a"]
            pb = aspect["point_b"]

            # Аспект должен быть между двумя разными картами
            is_cross = (pa in names_a and pb in names_b) or (pa in names_b and pb in names_a)

            if is_cross:
                # Определяем, кто из какой карты
                if pa in names_a:
                    point_a_chart = "A"
                    point_b_chart = "B"
                else:
                    point_a_chart = "B"
                    point_b_chart = "A"

                aspect_name = aspect["aspect"]
                score = self.ASPECT_SCORES.get(aspect_name, 0)

                synastry_aspects.append({
                    "point_a": pa,
                    "point_b": pb,
                    "point_a_chart": point_a_chart,
                    "point_b_chart": point_b_chart,
                    "aspect": aspect_name,
                    "orb": aspect["orb"],
                    "score": score,
                })

        # Сортируем по абсолютному значению орба (самые точные аспекты сверху)
        synastry_aspects.sort(key=lambda x: abs(x["orb"]))

        # Вычисляем оценку совместимости
        total_score = sum(a["score"] for a in synastry_aspects)

        # Максимально возможная оценка (если все аспекты гармоничные)
        # Упрощённо: количество возможных аспектов * средний балл за гармонию
        num_possible = len(objects_a) * len(objects_b)
        max_score = num_possible * 8  # 8 = средний балл за тригон

        # Нормализуем в 0-100%
        if max_score > 0:
            # Сдвигаем диапазон: min_score может быть отрицательным
            min_score = -max_score * 0.3  # допускаем до 30% негатива
            normalized = (total_score - min_score) / (max_score - min_score) * 100
            compatibility_percentage = max(0, min(100, normalized))
        else:
            compatibility_percentage = 50.0

        chart_a_name = chart_a.get("birth", {}).get("name", "Человек A")
        chart_b_name = chart_b.get("birth", {}).get("name", "Человек B")

        return SynastryResult(
            chart_a_name=chart_a_name,
            chart_b_name=chart_b_name,
            aspects=synastry_aspects,
            total_score=total_score,
            max_possible_score=max_score,
            compatibility_percentage=compatibility_percentage,
        )

    def get_interpretation(self, aspect_name: str) -> str:
        """Возвращает интерпретацию аспекта."""
        interpretations = {
            "conjunction": "Сильное соединение энергий, усиление обеих планет.",
            "sextile": "Гармоничное взаимодействие, лёгкость в использовании.",
            "square": "Напряжение, требующее усилий для интеграции.",
            "trine": "Естественная гармония, поток энергии без усилий.",
            "opposition": "Противоположные силы, необходимость баланса.",
        }
        return interpretations.get(aspect_name, "Аспект")