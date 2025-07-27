from __future__ import annotations
import os
import signal
import time
from collections import deque
from alert_utils import ALERTS
from monitoring import ERROR_COUNTER
import config

class ErrorManager:
    """Track recurring errors and stop the bot if threshold exceeded."""
    def __init__(self, *, window: float = 60.0, limit: int | None = None) -> None:
        self.window = window
        self.limit = limit or config.ERROR_LIMIT
        self.errors: deque[float] = deque()

    def record(self) -> None:
        now = time.time()
        self.errors.append(now)
        ERROR_COUNTER.labels(type="runtime").inc()
        self._trim(now)
        if len(self.errors) >= self.limit:
            ALERTS.error(
                f"Слишком много ошибок: {len(self.errors)} за {self.window} сек"
            )
            os.kill(os.getpid(), signal.SIGTERM)

    def _trim(self, now: float) -> None:
        while self.errors and now - self.errors[0] > self.window:
            self.errors.popleft()

ERROR_TRACKER = ErrorManager()
