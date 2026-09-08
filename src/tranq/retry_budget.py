import time
import threading
from collections import deque


class RetryBudget:
    """Token-based retry budget to prevent retry storms.

    Every normal call deposits a token; every retry consumes one. When the
    budget is empty, retries are rejected (fail-fast), protecting downstream
    services from cascading retry amplification.
    """

    def __init__(self, ttl: float = 60.0, ratio: float = 0.2, min_tokens: int = 10):
        self.ttl = ttl
        self.ratio = ratio
        self.min_tokens = min_tokens
        self._calls = deque()
        self._retries = deque()
        self._lock = threading.Lock()

    def _expire(self, now: float) -> None:
        cutoff = now - self.ttl
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()
        while self._retries and self._retries[0] < cutoff:
            self._retries.popleft()

    def record_call(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._expire(now)
            self._calls.append(now)

    def allow_retry(self) -> bool:
        with self._lock:
            now = time.monotonic()
            self._expire(now)
            tokens = max(self.min_tokens, len(self._calls) * self.ratio)
            if len(self._retries) < tokens:
                self._retries.append(now)
                return True
            return False

    def stats(self) -> dict:
        with self._lock:
            now = time.monotonic()
            self._expire(now)
            return {"calls": len(self._calls), "retries": len(self._retries)}


_DEFAULT_BUDGET = None
_budget_lock = threading.Lock()


def set_default_retry_budget(budget) -> None:
    global _DEFAULT_BUDGET
    with _budget_lock:
        _DEFAULT_BUDGET = budget


def get_default_retry_budget():
    with _budget_lock:
        return _DEFAULT_BUDGET
