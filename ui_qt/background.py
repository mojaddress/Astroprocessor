"""Фоновые расчёты: один рабочий поток, прогресс, отмена, перехват ошибок.

Зачем: точные транзиты за год занимают ~11.4 с (замер 13.11.2026) и блокируют UI.

Важно (Swiss Ephemeris не потокобезопасна из-за глобального состояния):
  * все фоновые задачи идут последовательно в ОДНОМ потоке (maxThreadCount=1);
  * на время задачи синхронные расчёты в главном потоке должны быть запрещены
    на уровне UI (кнопки/автопересчёты), иначе возможен одновременный доступ.
"""
from __future__ import annotations

import threading
import traceback
from typing import Any, Callable

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class TaskCancelled(Exception):
    """Задача прервана пользователем."""


class CancelToken:
    """Флаг отмены, проверяемый задачей в безопасных точках."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise TaskCancelled()


class _Signals(QObject):
    progress = pyqtSignal(int, str)
    done = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()
    finished = pyqtSignal()


class _Task(QRunnable):
    def __init__(self, fn: Callable, token: CancelToken, signals: _Signals) -> None:
        super().__init__()
        self._fn = fn
        self._token = token
        self.signals = signals

    def run(self) -> None:  # исполняется в рабочем потоке
        try:
            def report(percent: int, message: str = "") -> None:
                self._token.raise_if_cancelled()
                self.signals.progress.emit(int(percent), str(message))

            result = self._fn(self._token, report)
        except TaskCancelled:
            self.signals.cancelled.emit()
        except Exception:  # noqa: BLE001 - ошибка задачи не должна ронять UI
            self.signals.failed.emit(traceback.format_exc(limit=6))
        else:
            if self._token.cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.done.emit(result)
        finally:
            self.signals.finished.emit()


class BackgroundRunner(QObject):
    """Одиночный исполнитель фоновых задач: последовательно, с отменой."""

    busy_changed = pyqtSignal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._token: CancelToken | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def submit(
        self,
        fn: Callable,
        on_done: Callable[[Any], None] | None = None,
        on_progress: Callable[[int, str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_cancelled: Callable[[], None] | None = None,
        on_finished: Callable[[], None] | None = None,
    ) -> CancelToken:
        """Ставит задачу в работу. fn(token, report) -> результат."""
        if self._busy:
            raise RuntimeError("Задача уже выполняется: дождитесь завершения или отмените её")
        token = CancelToken()
        signals = _Signals()
        if on_progress is not None:
            signals.progress.connect(on_progress)
        if on_done is not None:
            signals.done.connect(on_done)
        if on_error is not None:
            signals.failed.connect(on_error)
        if on_cancelled is not None:
            signals.cancelled.connect(on_cancelled)

        def _finish() -> None:
            self._busy = False
            self._token = None
            self.busy_changed.emit(False)
            if on_finished is not None:
                on_finished()

        signals.finished.connect(_finish)
        self._token = token
        self._busy = True
        self.busy_changed.emit(True)
        self._pool.start(_Task(fn, token, signals))
        return token

    def cancel(self) -> None:
        if self._token is not None:
            self._token.cancel()

    def wait(self, msecs: int = 30000) -> bool:
        return self._pool.waitForDone(msecs)