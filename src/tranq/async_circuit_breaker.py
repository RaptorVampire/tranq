"""Async circuit breaker using asyncio.Lock and time.monotonic."""
import asyncio
import time


class AsyncCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0,
                 half_open_requests: int = 1, event_bus=None, name: str = None):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        self.event_bus = event_bus
        self.name = name or "async_circuit_breaker"
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "closed"
        self._half_open_allowed = half_open_requests
        self._lock = asyncio.Lock()

    def _emit(self, kind):
        if self.event_bus is not None:
            try:
                from . import events as ev
                mapping = {"open": ev.CircuitOpened, "closed": ev.CircuitClosed,
                           "half-open": ev.CircuitHalfOpened}
                cls = mapping.get(kind)
                if cls:
                    self.event_bus.publish(cls(breaker=self.name))
            except Exception:
                pass

    async def allow_request(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            if self._state == "closed":
                return True
            elif self._state == "open":
                if now - self._last_failure_time >= self.timeout:
                    self._state = "half-open"
                    self._half_open_allowed = self.half_open_requests
                    self._emit("half-open")
                    if self._half_open_allowed > 0:
                        self._half_open_allowed -= 1
                        return True
                return False
            else:
                if self._half_open_allowed > 0:
                    self._half_open_allowed -= 1
                    return True
                return False

    async def record_success(self):
        async with self._lock:
            if self._state == "half-open":
                self._state = "closed"
                self._failure_count = 0
                self._emit("closed")

    async def record_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == "closed" and self._failure_count >= self.failure_threshold:
                self._state = "open"
                self._emit("open")
            elif self._state == "half-open":
                self._state = "open"
                self._emit("open")

    async def reset(self):
        async with self._lock:
            self._state = "closed"
            self._failure_count = 0
            self._half_open_allowed = self.half_open_requests

    @property
    async def failure_count(self):
        async with self._lock:
            return self._failure_count

    @property
    async def state(self):
        async with self._lock:
            return self._state
