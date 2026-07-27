import time
import threading
from .exceptions import CircuitBreakerError

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0, half_open_requests: int = 1):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "closed"
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
                    return True
                return False
            # half-open
            if self._half_open_allowed > 0:
                self._half_open_allowed -= 1
                return True
            return False

    def record_success(self):
        with self._lock:
            if self._state == "half-open":
                self._state = "closed"
                self._failure_count = 0

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == "closed" and self._failure_count >= self.failure_threshold:
                self._state = "open"
            elif self._state == "half-open":
                self._state = "open"

    @property
    def state(self) -> str:
        with self._lock:
            return self._state
