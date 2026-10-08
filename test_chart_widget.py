"""
Быстрый тест векторного рендеринга карты без запуска GUI-сессии.
Сохраняет PNG с натальной картой для визуальной проверки:
- все ли символы планет/узлов/Хирона на месте
- гладкие ли линии при зуме
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui_qt.widgets.chart_view import ChartView

app = QApplication(sys.argv)

# Тестовые данные с полной палитрой объектов
data = {
    "planets": [
        {"name": "Sun", "longitude": 45, "sign": "Taurus", "retrograde": False},
        {"name": "Moon", "longitude": 120, "sign": "Leo", "retrograde": False},
        {"name": "Mercury", "longitude": 52, "sign": "Taurus", "retrograde": False},
        {"name": "Venus", "longitude": 80, "sign": "Gemini", "retrograde": False},
        {"name": "Mars", "longitude": 200, "sign": "Libra", "retrograde": False},
        {"name": "Jupiter", "longitude": 250, "sign": "Sagittarius", "retrograde": True},
        {"name": "Saturn", "longitude": 300, "sign": "Aquarius", "retrograde": False},
        {"name": "Uranus", "longitude": 30, "sign": "Taurus", "retrograde": False},
        {"name": "Neptune", "longitude": 350, "sign": "Pisces", "retrograde": False},
        {"name": "Pluto", "longitude": 295, "sign": "Capricorn", "retrograde": False},
        {"name": "MeanNode", "longitude": 150, "sign": "Virgo", "retrograde": False},
        {"name": "Chiron", "longitude": 20, "sign": "Aries", "retrograde": False},
    ],
    "houses": [{"house": i + 1, "longitude": i * 30} for i in range(12)],
    "aspects": [
        {"point_a": "Sun", "point_b": "Mars", "aspect": "opposition"},
        {"point_a": "Moon", "point_b": "Jupiter", "aspect": "trine"},
    ],
    "additional_points": [
        {"name": "ASC", "longitude": 0},
        {"name": "MC", "longitude": 270},
    ],
}

view = ChartView()
view.resize(1200, 1200)
view.set_chart_data(data)

output = "chart_check.png"
pixmap = view.grab()
pixmap.save(output)
print(f"✅ OK: {output} сохранён (размер: {pixmap.width()}x{pixmap.height()})")
print("Откройте файл и проверьте:")
print("  • Символы ☉ ☽ ☿ ♀ ♂ ♃ ♄ ♅ ♆ ♇ ☊ ⚷ должны быть видны")
print("  • Линии кругов должны быть идеально гладкими")
print("  • Красный маркер ретроградности у Юпитера")