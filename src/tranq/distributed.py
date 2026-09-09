"""Distributed resilience state: pluggable backends (in-memory, Redis).

These primitives allow rate limits, circuit breakers and retry budgets to be
shared across processes. The default backend is in-memory (single process);
``RedisBackend`` enables cluster-wide state when ``redis`` is installed.
"""
import time
import threading


class StateBackend:
    """Abstract key-value state backend with atomic increment."""

    def incr(self, key: str, amount: int = 1) -> int:
        raise NotImplementedError

    def get(self, key: str, default=0):
        raise NotImplementedError

    def set(self, key: str, value):
        raise NotImplementedError

    def expire(self, key: str, ttl: float):
        raise NotImplementedError


class InMemoryBackend(StateBackend):
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def incr(self, key, amount=1):
        with self._lock:
            self._data[key] = self._data.get(key, 0) + amount
            return self._data[key]

    def get(self, key, default=0):
        with self._lock:
            return self._data.get(key, default)

    def set(self, key, value):
        with self._lock:
            self._data[key] = value

    def expire(self, key, ttl):
        pass  # no-op for in-memory


class RedisBackend(StateBackend):
    """Redis-backed state (requires the ``redis`` package)."""

    def __init__(self, url: str = "redis://localhost:6379/0"):
        import redis
        self._client = redis.Redis.from_url(url)

    def incr(self, key, amount=1):
        return self._client.incrby(key, amount)

    def get(self, key, default=0):
        v = self._client.get(key)
        return int(v) if v is not None else default

    def set(self, key, value):
        self._client.set(key, value)

    def expire(self, key, ttl):
        self._client.expire(key, int(ttl))


class DistributedRateLimiter:
    """Fixed-window rate limiter shared across processes via a backend."""

    def __init__(self, limit: int, window: float = 1.0, backend: StateBackend = None,
                 key: str = "tranq:rl"):
        self.limit = limit
        self.window = window
        self.backend = backend or InMemoryBackend()
        self.key = key

    def _window_key(self):
        return f"{self.key}:{int(time.monotonic() // self.window)}"

    def try_acquire(self) -> bool:
        k = self._window_key()
        count = self.backend.incr(k)
        if count == 1:
            self.backend.expire(k, self.window + 1)
        return count <= self.limit


class DistributedCounter:
    """Shared counter (e.g. for a cluster-wide retry budget)."""

    def __init__(self, backend: StateBackend = None, key: str = "tranq:counter"):
        self.backend = backend or InMemoryBackend()
        self.key = key

    def incr(self, amount: int = 1) -> int:
        return self.backend.incr(self.key, amount)

    def get(self) -> int:
        return self.backend.get(self.key)
