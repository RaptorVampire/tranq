import time
import asyncio
import inspect
import functools
import threading

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

    def _refill(self) -> None:
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
        deadline = None if timeout is None else time.monotonic() + deadline_delta(timeout)
        while True:
            if self.try_acquire():
                return True
            if deadline is not None and time.monotonic() >= deadline:
                return False
            await asyncio.sleep(0.01)


def deadline_delta(timeout):
    return timeout if timeout is not None else 0


def rate_limit(rate: float, per: float = 1.0, burst: int = None,
               timeout: float = None, raise_on_limit: bool = True,
               limiter: RateLimiter = None):
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
