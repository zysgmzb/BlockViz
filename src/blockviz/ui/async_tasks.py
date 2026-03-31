"""Small helpers for running blocking work off the UI thread."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

_ACTIVE_TASKS: set["BackgroundTask"] = set()


class BackgroundTaskSignals(QObject):
    """Signals emitted by a background task."""

    succeeded = Signal(object)
    failed = Signal(object)


class BackgroundTask(QRunnable):
    """Runs a callable on the global Qt thread pool."""

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn
        self.signals = BackgroundTaskSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001
            self.signals.failed.emit(exc)
            return
        self.signals.succeeded.emit(result)


def run_in_background(
    fn: Callable[[], Any],
    *,
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None] | None = None,
) -> BackgroundTask:
    """Schedule work on the Qt global thread pool."""
    task = BackgroundTask(fn)
    _ACTIVE_TASKS.add(task)

    def cleanup(*_args: object) -> None:
        _ACTIVE_TASKS.discard(task)

    task.signals.succeeded.connect(on_success)
    task.signals.succeeded.connect(cleanup)
    if on_error is not None:
        task.signals.failed.connect(on_error)
    task.signals.failed.connect(cleanup)
    QThreadPool.globalInstance().start(task)
    return task
