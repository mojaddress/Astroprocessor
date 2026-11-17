"""Замер стоимости кадра анимации транзитов (ползунок времени).

Запуск: py -3.11 bench_animation.py
Оговорка: offscreen-рендер измеряет построение сцены и растеризацию;
реальная отрисовка на экране может отличаться. Это нижняя оценка стоимости.
"""
from __future__ import annotations

import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QApplication

from astro_core.chart import build_natal_chart
from ui_qt.main_window import MainWindow

BIRTH = {
    "name": "Bench", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}
FRAMES = 60
BUDGET_MS = 40.0


def main() -> int:
    app = QApplication.instance() or QApplication([])
    chart = build_natal_chart(BIRTH, {})
    window = MainWindow()
    window._current_chart_result = chart
    window._current_birth_data = BIRTH
    window.resize(1400, 900)
    window.show()
    app.processEvents()

    anchor = QDate(2026, 1, 1)
    window._time_slider.set_anchor(anchor)
    window._slider_pending = anchor
    window._apply_slider_date()
    app.processEvents()

    start = time.perf_counter()
    for index in range(FRAMES):
        window._transit_layer(anchor.addDays(index))
    data_ms = (time.perf_counter() - start) * 1000 / FRAMES

    start = time.perf_counter()
    for index in range(FRAMES):
        window._slider_pending = anchor.addDays(index)
        window._apply_slider_date()
        app.processEvents()
    full_ms = (time.perf_counter() - start) * 1000 / FRAMES

    render_ms = max(0.0, full_ms - data_ms)
    print("=" * 74)
    print(f"Кадров в замере: {FRAMES}")
    print(f"Данные (эфемериды + аспекты):      {data_ms:8.2f} мс")
    print(f"Перерисовка сцены:                {render_ms:8.2f} мс")
    print(f"Полный кадр:                      {full_ms:8.2f} мс")
    print(f"Бюджет троттлинга:                {BUDGET_MS:8.2f} мс (25 кадров/с)")
    if full_ms <= BUDGET_MS:
        print(f"ВЕРДИКТ: укладывается, запас {BUDGET_MS / full_ms:.1f}x")
    else:
        print(f"ВЕРДИКТ: НЕ укладывается, нужен шаг {full_ms:.0f} мс "
              f"({1000 / full_ms:.1f} кадров/с) или оптимизация сцены")
    print("=" * 74)
    window._time_slider.stop()
    window.deleteLater()
    return 0


if __name__ == "__main__":
    sys.exit(main())