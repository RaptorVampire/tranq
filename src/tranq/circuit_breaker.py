"""Synchronous circuit breaker with slow-call detection, state-change events
and a shared breaker registry.
"""
import time
import threading


class CircuitBreaker:
    """Count-based circuit breaker: closed -> open -> half-open -> closed.

    Optional slow-call detection: calls slower than ``slow_call_duration`` are
    counted as slow; the breaker opens when the slow-call rate exceeds
    ``slow_call_rate_threshold``.
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0,
                 half_open_requests: int = 1, slow_call_duration: float = None,
                 slow_call_rate_threshold: float = 1.0, minimum_calls: int = 1,
                 event_bus=None, name: str = None):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        self.slow_call_duration = slow_call_duration
        self.slow_call_rate_threshold = slow_call_rate_threshold
        self.minimum_calls = minimum_calls
        self.event_bus = event_bus
        self.name = name or "circuit_breaker"
        self._failure_count = 0
        self._slow_count = 0
        self._total_count = 0
        self._last_failure_time = 0.0
        self._state = "closed"
        self._half_open_allowed = half_open_requests
        self._lock = threading.Lock()

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

    def allow_request(self) -> bool:
        with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if time.monotonic() - self._last_failure_time >= self.timeout:
                    self._state = "half-open"
                    self._half_open_allowed = self.half_open_requests
                    self._emit("half-open")
                    if self._half_open_allowed > 0:
                        self._half_open_allowed -= 1
                        return True
                return False
            if self._half_open_allowed > 0:
                self._half_open_allowed -= 1
                return True
            return False

    def record_success(self, duration: float = None):
        with self._lock:
            self._total_count += 1
            if duration is not None and self.slow_call_duration is not None:
                if duration >= self.slow_call_duration:
                    self._slow_count += 1
            if self._state == "half-open":
                self._state = "closed"
                self._failure_count = 0
                self._slow_count = 0
                self._total_count = 0
                self._emit("closed")

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._total_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == "closed":
                if self._failure_count >= self.failure_threshold:
                    self._state = "open"
                    self._emit("open")
                else:
                    self._maybe_open_on_slow()
            elif self._state == "half-open":
                self._state = "open"
                self._emit("open")

    def _maybe_open_on_slow(self):
        if self.slow_call_duration is None:
            return
        if self._total_count < self.minimum_calls:
            return
        rate = self._slow_count / self._total_count if self._total_count else 0.0
        if rate >= self.slow_call_rate_threshold:
            self._state = "open"
            self._emit("open")

    def reset(self):
        with self._lock:
            self._state = "closed"
            self._failure_count = 0
            self._slow_count = 0
            self._total_count = 0
            self._half_open_allowed = self.half_open_requests

    @property
    def failure_count(self):
        with self._lock:
            return self._failure_count

    @property
    def state(self):
        with self._lock:
            return self._state


class BreakerRegistry:
    """Shared registry of named circuit breakers (per-service breakers)."""

    def __init__(self):
        self._breakers = {}
        self._lock = threading.Lock()

    def get(self, name: str, **kwargs) -> CircuitBreaker:
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name=name, **kwargs)
            return self._breakers[name]

    def all(self):
        with self._lock:
            return dict(self._breakers)

    def states(self):
        return {name: cb.state for name, cb in self.all().items()}


_registry = BreakerRegistry()


def get_registry() -> BreakerRegistry:
    return _registry
