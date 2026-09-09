"""Rate limiting algorithms: token bucket, leaky bucket, fixed window,
sliding window and adaptive rate limiting. All are thread-safe.
"""
import time
import asyncio
import inspect
import functools
import threading
from collections import deque

from .exceptions import RateLimitExceeded


class RateLimiter:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, rate: float, per: float = 1.0, burst: int = None):
        self.rate = rate
        self.per = per
        self.capacity = burst if burst is not None else max(1, int(rate))
        self._tokens = float(self.capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * (self.rate / self.per))

    def try_acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def acquire(self, timeout: float = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if self.try_acquire():
                return True
            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(0.01)

    async def acquire_async(self, timeout: float = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if self.try_acquire():
                return True
            if deadline is not None and time.monotonic() >= deadline:
                return False
            await asyncio.sleep(0.01)


class LeakyBucket:
    """Leaky bucket: requests drain at a fixed rate."""

    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self._water = 0.0
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _leak(self):
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        self._water = max(0.0, self._water - elapsed * self.leak_rate)

    def try_acquire(self) -> bool:
        with self._lock:
            self._leak()
            if self._water + 1 <= self.capacity:
                self._water += 1
                return True
            return False


class FixedWindowLimiter:
    """Fixed window counter limiter."""

    def __init__(self, limit: int, window: float = 1.0):
        self.limit = limit
        self.window = window
        self._count = 0
        self._window_start = time.monotonic()
        self._lock = threading.Lock()

    def try_acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            if now - self._window_start >= self.window:
                self._window_start = now
                self._count = 0
            if self._count < self.limit:
                self._count += 1
                return True
            return False


class SlidingWindowLimiter:
    """Sliding window log limiter (precise)."""

    def __init__(self, limit: int, window: float = 1.0):
        self.limit = limit
        self.window = window
        self._log = deque()
        self._lock = threading.Lock()

    def try_acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window
            while self._log and self._log[0] <= cutoff:
                self._log.popleft()
            if len(self._log) < self.limit:
                self._log.append(now)
                return True
            return False


class AdaptiveRateLimiter:
    """Rate limiter that adjusts its rate based on a success/failure signal.

    Call ``record_success()`` / ``record_failure()``. On failures the rate is
    multiplied down; on sustained success it recovers toward the base rate.
    """

    def __init__(self, base_rate: float, per: float = 1.0,
                 decrease_factor: float = 0.5, increase_factor: float = 1.1,
                 min_rate: float = 0.1):
        self.base_rate = base_rate
        self.per = per
        self.decrease_factor = decrease_factor
        self.increase_factor = increase_factor
        self.min_rate = min_rate
        self._current = base_rate
        self._inner = RateLimiter(base_rate, per)
        self._lock = threading.Lock()

    def _rebuild(self):
        self._inner = RateLimiter(max(self._current, self.min_rate), self.per)

    def record_failure(self):
        with self._lock:
            self._current = max(self.min_rate, self._current * self.decrease_factor)
            self._rebuild()

    def record_success(self):
        with self._lock:
            self._current = min(self.base_rate, self._current * self.increase_factor)
            self._rebuild()

    @property
    def current_rate(self):
        with self._lock:
            return self._current

    def try_acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            inner = self._inner
        return inner.try_acquire(tokens)

    def acquire(self, timeout: float = None) -> bool:
        with self._lock:
            inner = self._inner
        return inner.acquire(timeout)


def rate_limit(rate: float, per: float = 1.0, burst: int = None,
               timeout: float = None, raise_on_limit: bool = True,
               limiter=None):
    """Decorator throttling a sync or async function using a token bucket."""
    rl = limiter or RateLimiter(rate, per, burst)

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                ok = await rl.acquire_async(timeout=timeout)
                if not ok:
                    if raise_on_limit:
                        raise RateLimitExceeded(f"Rate limit exceeded for {func.__name__}")
                    return None
                return await func(*args, **kwargs)
            async_wrapper.rate_limiter = rl
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                ok = rl.acquire(timeout=timeout)
                if not ok:
                    if raise_on_limit:
                        raise RateLimitExceeded(f"Rate limit exceeded for {func.__name__}")
                    return None
                return func(*args, **kwargs)
            sync_wrapper.rate_limiter = rl
            return sync_wrapper

    return decorator
