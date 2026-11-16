"""Тесты фонового исполнителя: результат, прогресс, ошибка, отмена, последовательность."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import time

import pytest
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication

from ui_qt.background import BackgroundRunner, CancelToken, TaskCancelled


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def runner(qapp):
    r = BackgroundRunner()
    yield r
    r.cancel()
    r.wait(5000)


def execute(runner, fn, timeout_ms=5000, cancel_after_ms=None):
    out = {"progress": []}
    loop = QEventLoop()

    def on_done(value):
        out["done"] = value

    def on_error(text):
        out["error"] = text

    def on_cancelled():
        out["cancelled"] = True

    def on_progress(percent, message):
        out["progress"].append((percent, message))

    def on_finished():
        loop.quit()

    runner.submit(fn, on_done=on_done, on_progress=on_progress,
                  on_error=on_error, on_cancelled=on_cancelled, on_finished=on_finished)
    if cancel_after_ms is not None:
        QTimer.singleShot(cancel_after_ms, runner.cancel)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    return out


def test_success_delivers_result(runner):
    out = execute(runner, lambda token, report: 42)
    assert out.get("done") == 42
    assert "error" not in out


def test_progress_reports_delivered(runner):
    def fn(token, report):
        for p in (0, 50, 100):
            report(p, f"шаг {p}")
        return "ok"

    out = execute(runner, fn)
    assert [p for p, _ in out["progress"]] == [0, 50, 100]
    assert out.get("done") == "ok"


def test_error_is_captured_not_raised(runner):
    def fn(token, report):
        raise ValueError("boom")

    out = execute(runner, fn)
    assert "boom" in out.get("error", "")
    assert "done" not in out


def test_cancel_stops_task(runner):
    def fn(token, report):
        for _ in range(400):
            token.raise_if_cancelled()
            time.sleep(0.005)
        return "not reached"

    out = execute(runner, fn, cancel_after_ms=60)
    assert out.get("cancelled") is True
    assert "done" not in out


def test_busy_guard_rejects_second_task(runner):
    def slow(token, report):
        for _ in range(200):
            token.raise_if_cancelled()
            time.sleep(0.005)
        return 1

    runner.submit(slow)
    assert runner.busy is True
    with pytest.raises(RuntimeError):
        runner.submit(lambda token, report: 2)
    runner.cancel()
    assert runner.wait(5000)


def test_busy_reset_after_completion(runner):
    execute(runner, lambda token, report: 1)
    assert runner.busy is False


def test_sequential_tasks_reuse_pool(runner):
    assert execute(runner, lambda token, report: "a").get("done") == "a"
    assert execute(runner, lambda token, report: "b").get("done") == "b"


def test_cancel_token_semantics():
    token = CancelToken()
    token.raise_if_cancelled()
    token.cancel()
    assert token.cancelled is True
    with pytest.raises(TaskCancelled):
        token.raise_if_cancelled()