"""Проброс progress/cancel через контроллер и расчёт в фоновом исполнителе."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication

from astro_core.chart import build_natal_chart
from astro_core.controllers import TransitController
from ui_qt.background import BackgroundRunner

BIRTH = {
    "name": "BgTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def controller():
    return TransitController()


@pytest.fixture(scope="module")
def natal():
    return build_natal_chart(BIRTH, {})["objects"]


def test_precise_progress_reaches_100(controller, natal):
    seen = []
    controller.calculate_transits(
        natal, "2026-01-01", "2026-01-05", controller.get_default_settings(),
        mode="precise", progress=lambda p, m: seen.append(p))
    assert seen and seen[-1] == 100


def test_periods_progress_reaches_100(controller, natal):
    seen = []
    controller.calculate_transits(
        natal, "2026-01-01", "2026-01-05", controller.get_default_settings(),
        mode="periods", progress=lambda p, m: seen.append(p))
    assert seen and seen[-1] == 100


def test_cancel_propagates_through_controller(controller, natal):
    def cancel():
        raise RuntimeError("cancelled")

    with pytest.raises(RuntimeError):
        controller.calculate_transits(
            natal, "2026-01-01", "2026-01-10", controller.get_default_settings(),
            mode="precise", cancel=cancel)


def test_calendar_accepts_callbacks_without_effect(controller, natal):
    result = controller.calculate_transits(
        natal, "2026-01-01", "2026-01-03", controller.get_default_settings(),
        mode="calendar", progress=lambda p, m: None, cancel=lambda: None)
    assert isinstance(result, list)


def test_background_executes_controller(qapp, controller, natal):
    runner = BackgroundRunner()
    outcome = {}
    loop = QEventLoop()
    settings = controller.get_default_settings()

    def task(token, report):
        return controller.calculate_transits(
            natal, "2026-01-01", "2026-01-10", settings, mode="precise",
            progress=report, cancel=token.raise_if_cancelled)

    def done(value):
        outcome["done"] = value

    def finished():
        loop.quit()

    runner.submit(task, on_done=done, on_finished=finished)
    QTimer.singleShot(15000, loop.quit)
    loop.exec()
    assert isinstance(outcome.get("done"), list)
    assert runner.busy is False
