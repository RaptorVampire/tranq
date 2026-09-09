"""In-memory resilience cache with TTL, LRU eviction, stampede prevention,
stale-if-error, negative caching and cache metrics. Thread and asyncio safe.
"""
import time
import asyncio
import hashlib
import inspect
import threading
from collections import OrderedDict


def make_key(func, args, kwargs):
    """Build a deterministic cache key from a function call."""
    try:
        raw = repr((func.__module__, func.__name__, args, tuple(sorted(kwargs.items()))))
    except Exception:
        raw = repr((getattr(func, "__name__", str(func)), time.monotonic()))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


class _Entry:
    __slots__ = ("value", "created", "ttl", "negative")

    def __init__(self, value, ttl, negative=False):
        self.value = value
        self.created = time.monotonic()
        self.ttl = ttl
        self.negative = negative

    def fresh(self):
        return self.ttl is None or (time.monotonic() - self.created) < self.ttl


class TranqCache:
    """Thread-safe in-memory cache with TTL + LRU eviction."""

    def __init__(self, ttl: float = None, maxsize: int = 256,
                 negative_ttl: float = None, stale_if_error: bool = True):
        self.ttl = ttl
        self.maxsize = maxsize
        self.negative_ttl = negative_ttl
        self.stale_if_error = stale_if_error
        self._data = OrderedDict()
        self._lock = threading.Lock()
        self._flights = {}
        self.stats = {"hits": 0, "misses": 0, "stale_hits": 0,
                      "negative_hits": 0, "evictions": 0, "sets": 0}

    def get(self, key):
        """Return (hit, value). Only returns fresh entries."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self.stats["misses"] += 1
                return False, None
            if entry.fresh():
                self._data.move_to_end(key)
                self.stats["hits"] += 1
                if entry.negative:
                    self.stats["negative_hits"] += 1
                return True, entry.value
            self.stats["misses"] += 1
            return False, None

    def get_stale(self, key):
        """Return (hit, value) even if the entry is expired (for stale-if-error)."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False, None
            self.stats["stale_hits"] += 1
            return True, entry.value

    def set(self, key, value, ttl=None, negative=False):
        with self._lock:
            effective_ttl = self.negative_ttl if negative else (ttl or self.ttl)
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = _Entry(value, effective_ttl, negative)
            self.stats["sets"] += 1
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)
                self.stats["evictions"] += 1

    def invalidate(self, key):
        with self._lock:
            self._data.pop(key, None)

    def clear(self):
        with self._lock:
            self._data.clear()

    def single_flight(self, key, loader):
        """Stampede prevention: only one caller loads a missing key.

        Other concurrent callers wait for the in-flight result.
        """
        with self._lock:
            if key in self._flights:
                event, holder = self._flights[key]
            else:
                event = threading.Event()
                holder = {}
                self._flights[key] = (event, holder)
                event = None  # signals this thread is the loader

        if event is not None:
            event.wait()
            if "error" in holder:
                raise holder["error"]
            return holder["value"]

        ev, holder = self._flights[key]
        try:
            value = loader()
            holder["value"] = value
            self.set(key, value)
            return value
        except Exception as e:
            holder["error"] = e
            raise
        finally:
            ev.set()
            with self._lock:
                self._flights.pop(key, None)

    def metrics(self):
        with self._lock:
            return dict(self.stats)


class AsyncTranqCache(TranqCache):
    """Asyncio-friendly cache (single_flight_async for stampede prevention)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aflights = {}

    async def single_flight_async(self, key, loader):
        loop = asyncio.get_event_loop()
        if key in self._aflights:
            return await self._aflights[key]

        async def _run():
            try:
                if inspect.iscoroutinefunction(loader):
                    value = await loader()
                else:
                    value = loader()
                self.set(key, value)
                return value
            finally:
                self._aflights.pop(key, None)

        task = asyncio.ensure_future(_run())
        self._aflights[key] = task
        return await task


def cache(ttl: float = None, maxsize: int = 256, cache_obj: TranqCache = None):
    """Decorator adding cache-aside semantics to a sync or async function."""
    store = cache_obj or TranqCache(ttl=ttl, maxsize=maxsize)

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            astore = cache_obj if isinstance(cache_obj, AsyncTranqCache) else AsyncTranqCache(ttl=ttl, maxsize=maxsize)

            async def aw(*args, **kwargs):
                key = make_key(func, args, kwargs)
                hit, val = astore.get(key)
                if hit:
                    return val
                return await astore.single_flight_async(key, lambda: func(*args, **kwargs))
            aw.cache = astore
            return aw
        else:
            def w(*args, **kwargs):
                key = make_key(func, args, kwargs)
                hit, val = store.get(key)
                if hit:
                    return val
                return store.single_flight(key, lambda: func(*args, **kwargs))
            w.cache = store
            return w
    return decorator
