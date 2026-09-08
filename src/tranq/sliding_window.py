import time
import asyncio
import threading
from collections import deque


class SlidingWindowCircuitBreaker:
    """Circuit breaker based on failure *rate* over a sliding window."""

    def __init__(self, window_size: int = 100, failure_rate_threshold: float = 0.5,
                 timeout: float = 60.0, half_open_requests: int = 1,
                 minimum_calls: int = 10):
        self.window_size = window_size
        self.failure_rate_threshold = failure_rate_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        self.minimum_calls = minimum_calls
        self._outcomes = deque(maxlen=window_size)
        self._state = "closed"
        self._last_failure_time = 0.0
        self._half_open_allowed = half_open_requests
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if time.monotonic() - self._last_failure_time >= self.timeout:
                    self._state = "half-open"
                    self._half_open_allowed = self.half_open_requests
                    if self._half_open_allowed > 0:
                        self._half_open_allowed -= 1
                        return True
                return False
            if self._half_open_allowed > 0:
                self._half_open_allowed -= 1
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            if self._state == "half-open":
                self._state = "closed"
                self._outcomes.clear()
            else:
                self._outcomes.append(True)

    def record_failure(self) -> None:
        with self._lock:
            self._last_failure_time = time.monotonic()
            if self._state == "half-open":
                self._state = "open"
                return
            self._outcomes.append(False)
            self._maybe_open()

    def _maybe_open(self) -> None:
        if len(self._outcomes) < self.minimum_calls:
            return
        failures = sum(1 for o in self._outcomes if not o)
        if failures / len(self._outcomes) >= self.failure_rate_threshold:
            self._state = "open"

    def reset(self) -> None:
        with self._lock:
            self._state = "closed"
            self._outcomes.clear()
            self._half_open_allowed = self.half_open_requests

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def failure_rate(self) -> float:
        with self._lock:
            if not self._outcomes:
                return 0.0
            return sum(1 for o in self._outcomes if not o) / len(self._outcomes)


class AsyncSlidingWindowCircuitBreaker:
    """Async version of the sliding-window (failure-rate) circuit breaker."""

    def __init__(self, window_size: int = 100, failure_rate_threshold: float = 0.5,
                 timeout: float = 60.0, half_open_requests: int = 1,
                 minimum_calls: int = 10):
        self.window_size = window_size
        self.failure_rate_threshold = failure_rate_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        self.minimum_calls = minimum_calls
        self._outcomes = deque(maxlen=window_size)
        self._state = "closed"
        self._last_failure_time = 0.0
        self._half_open_allowed = half_open_requests
        self._lock = asyncio.Lock()

    async def allow_request(self) -> bool:
        async with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if time.monotonic() - self._last_failure_time >= self.timeout:
                    self._state = "half-open"
                    self._half_open_allowed = self.half_open_requests
                    if self._half_open_allowed > 0:
                        self._half_open_allowed -= 1
                        return True
                return False
            if self._half_open_allowed > 0:
                self._half_open_allowed -= 1
                return True
            return False

    async def record_success(self) -> None:
        async with self._lock:
            if self._state == "half-open":
                self._state = "closed"
                self._outcomes.clear()
            else:
                self._outcomes.append(True)

    async def record_failure(self) -> None:
        async with self._lock:
            self._last_failure_time = time.monotonic()
            if self._state == "half-open":
                self._state = "open"
                return
            self._outcomes.append(False)
            if len(self._outcomes) >= self.minimum_calls:
                failures = sum(1 for o in self._outcomes if not o)
                if failures / len(self._outcomes) >= self.failure_rate_threshold:
                    self._state = "open"

    async def reset(self) -> None:
        async with self._lock:
            self._state = "closed"
            self._outcomes.clear()
            self._half_open_allowed = self.half_open_requests

    @property
    async def state(self) -> str:
        async with self._lock:
            return self._state

    @property
    async def failure_rate(self) -> float:
        async with self._lock:
            if not self._outcomes:
                return 0.0
            return sum(1 for o in self._outcomes if not o) / len(self._outcomes)
