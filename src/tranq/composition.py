"""Policy composition DSL: build resilience policies fluently.

Example:
    policy = (
        tranq.PolicyBuilder()
        .timeout(5)
        .retry(max_attempts=3, wait=wait.exponential(0.5, max=10))
        .circuit_breaker(cb)
        .rate_limit(rate=10)
        .bulkhead(max_concurrent=5)
        .fallback(lambda: "cached")
        .cache(ttl=60)
        .observe(event_bus=bus)
    )

    @policy
    def call_service():
        ...
"""
import time
import inspect
import functools

from .cache import TranqCache, AsyncTranqCache, make_key
from .rate_limiter import RateLimiter
from .bulkhead import Bulkhead, AsyncBulkhead
from .fallback import FallbackChain
from .exceptions import CircuitBreakerError, RateLimitExceeded, BulkheadFullError
from . import events as _events


class ResiliencePolicy:
    """A composed resilience policy that decorates sync or async functions.

    Execution order (outermost first):
        cache -> rate limit -> bulkhead -> circuit breaker
              -> retry loop (timeout + wait + stop + retry_if)
              -> fallback / stale-if-error -> cache store
    """

    def __init__(self, config: dict):
        self.config = config

    def __call__(self, func):
        if inspect.iscoroutinefunction(func):
            return self._wrap_async(func)
        return self._wrap_sync(func)

    # ---- sync ----
    def _wrap_sync(self, func):
        c = self.config
        cache = c.get("cache")
        rate_limiter = c.get("rate_limiter")
        bulk = c.get("bulkhead")
        cb = c.get("circuit_breaker")
        wait = c.get("wait")
        stop = c.get("stop")
        retry_if = c.get("retry_if")
        timeout = c.get("timeout")
        fallback = c.get("fallback")
        bus = c.get("event_bus")
        max_attempts = c.get("max_attempts", 1)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = make_key(func, args, kwargs)

            # cache lookup
            if cache is not None:
                hit, val = cache.get(key)
                if hit:
                    if bus:
                        bus.publish(_events.CacheHitEvent(key=key))
                    return val
                if bus:
                    bus.publish(_events.CacheMissEvent(key=key))

            # rate limit
            if rate_limiter is not None:
                if not rate_limiter.try_acquire():
                    if bus:
                        bus.publish(_events.RateLimitExceededEvent(func=func.__name__))
                    if fallback is not None:
                        return self._call_fallback(fallback, args, kwargs)
                    raise RateLimitExceeded(f"Rate limit exceeded for {func.__name__}")

            # bulkhead
            if bulk is not None:
                if not bulk.acquire():
                    if bus:
                        bus.publish(_events.BulkheadRejectedEvent(func=func.__name__))
                    if fallback is not None:
                        return self._call_fallback(fallback, args, kwargs)
                    raise BulkheadFullError(f"Bulkhead full for {func.__name__}")
            try:
                return self._run_sync(func, args, kwargs, key, cache, cb, wait, stop,
                                      retry_if, timeout, fallback, bus, max_attempts)
            finally:
                if bulk is not None:
                    bulk.release()

        return wrapper

    def _run_sync(self, func, args, kwargs, key, cache, cb, wait, stop,
                  retry_if, timeout, fallback, bus, max_attempts):
        attempt = 0
        start = time.monotonic()
        last = None
        while True:
            attempt += 1
            try:
                if cb is not None and not cb.allow_request():
                    raise CircuitBreakerError("Circuit breaker is open")
                t0 = time.perf_counter()
                if timeout is not None:
                    from .utils import run_with_timeout
                    result = run_with_timeout(func, args, kwargs, timeout)
                else:
                    result = func(*args, **kwargs)
                dur = time.perf_counter() - t0
                if cb is not None:
                    cb.record_success(dur)
                if cache is not None:
                    cache.set(key, result)
                if bus:
                    bus.publish(_events.OperationSucceeded(func=func.__name__))
                return result
            except Exception as e:
                last = e
                if cb is not None and not isinstance(e, CircuitBreakerError):
                    cb.record_failure()
                if bus:
                    bus.publish(_events.OperationFailed(func=func.__name__, error=str(e)))
                elapsed = time.monotonic() - start
                should_retry = True
                if retry_if is not None:
                    should_retry = retry_if(e)
                if stop is not None:
                    if stop(attempt, elapsed):
                        should_retry = False
                elif attempt >= max_attempts:
                    should_retry = False
                if not should_retry:
                    break
                if bus:
                    bus.publish(_events.RetryStarted(func=func.__name__, attempt=attempt))
                delay = wait(attempt) if wait is not None else 0.0
                time.sleep(delay)

        # exhausted: stale-if-error, then fallback, then raise
        if cache is not None:
            hit, val = cache.get_stale(key)
            if hit:
                if bus:
                    bus.publish(_events.FallbackTriggered(func=func.__name__, source="cache"))
                return val
        if fallback is not None:
            if bus:
                bus.publish(_events.FallbackTriggered(func=func.__name__, source="fallback"))
            return self._call_fallback(fallback, args, kwargs)
        raise last

    def _call_fallback(self, fallback, args, kwargs):
        if isinstance(fallback, FallbackChain):
            return fallback.run(*args, **kwargs)
        if callable(fallback):
            return fallback(*args, **kwargs)
        return fallback

    # ---- async ----
    def _wrap_async(self, func):
        c = self.config
        cache = c.get("cache")
        rate_limiter = c.get("rate_limiter")
        bulk = c.get("bulkhead")
        cb = c.get("circuit_breaker")
        wait = c.get("wait")
        stop = c.get("stop")
        retry_if = c.get("retry_if")
        timeout = c.get("timeout")
        fallback = c.get("fallback")
        bus = c.get("event_bus")
        max_attempts = c.get("max_attempts", 1)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio as _aio
            key = make_key(func, args, kwargs)

            if cache is not None:
                hit, val = cache.get(key)
                if hit:
                    return val

            if rate_limiter is not None:
                ok = await rate_limiter.acquire_async(timeout=0) if hasattr(rate_limiter, "acquire_async") \
                    else rate_limiter.try_acquire()
                if not ok:
                    if fallback is not None:
                        return await self._call_fallback_async(fallback, args, kwargs)
                    raise RateLimitExceeded(f"Rate limit exceeded for {func.__name__}")

            if bulk is not None:
                if not await bulk.acquire():
                    if fallback is not None:
                        return await self._call_fallback_async(fallback, args, kwargs)
                    raise BulkheadFullError(f"Bulkhead full for {func.__name__}")
            try:
                attempt = 0
                start = time.monotonic()
                last = None
                while True:
                    attempt += 1
                    try:
                        if cb is not None:
                            allowed = await cb.allow_request() if inspect.iscoroutinefunction(cb.allow_request) else cb.allow_request()
                            if not allowed:
                                raise CircuitBreakerError("Circuit breaker is open")
                        if timeout is not None:
                            result = await _aio.wait_for(func(*args, **kwargs), timeout)
                        else:
                            result = await func(*args, **kwargs)
                        if cb is not None:
                            await cb.record_success() if inspect.iscoroutinefunction(cb.record_success) else cb.record_success()
                        if cache is not None:
                            cache.set(key, result)
                        return result
                    except Exception as e:
                        last = e
                        if cb is not None and not isinstance(e, CircuitBreakerError):
                            await cb.record_failure() if inspect.iscoroutinefunction(cb.record_failure) else cb.record_failure()
                        elapsed = time.monotonic() - start
                        should_retry = True
                        if retry_if is not None:
                            should_retry = retry_if(e)
                        if stop is not None:
                            if stop(attempt, elapsed):
                                should_retry = False
                        elif attempt >= max_attempts:
                            should_retry = False
                        if not should_retry:
                            break
                        delay = wait(attempt) if wait is not None else 0.0
                        await _aio.sleep(delay)

                if cache is not None:
                    hit, val = cache.get_stale(key)
                    if hit:
                        return val
                if fallback is not None:
                    return await self._call_fallback_async(fallback, args, kwargs)
                raise last
            finally:
                if bulk is not None:
                    bulk.release()

        return wrapper

    async def _call_fallback_async(self, fallback, args, kwargs):
        if isinstance(fallback, FallbackChain):
            return await fallback.run_async(*args, **kwargs)
        if inspect.iscoroutinefunction(fallback):
            return await fallback(*args, **kwargs)
        if callable(fallback):
            return fallback(*args, **kwargs)
        return fallback


class PolicyBuilder:
    """Fluent builder for a ResiliencePolicy."""

    def __init__(self):
        self._config = {}

    def retry(self, max_attempts: int = 3, wait=None, stop=None, retry_if=None):
        self._config["max_attempts"] = max_attempts
        if wait is not None:
            self._config["wait"] = wait
        if stop is not None:
            self._config["stop"] = stop
        if retry_if is not None:
            self._config["retry_if"] = retry_if
        return self

    def timeout(self, seconds: float):
        self._config["timeout"] = seconds
        return self

    def circuit_breaker(self, cb):
        self._config["circuit_breaker"] = cb
        return self

    def rate_limit(self, rate: float, per: float = 1.0, burst: int = None, limiter=None):
        self._config["rate_limiter"] = limiter or RateLimiter(rate, per, burst)
        return self

    def bulkhead(self, max_concurrent: int, timeout: float = None, instance=None):
        self._config["bulkhead"] = instance or Bulkhead(max_concurrent, timeout)
        return self

    def fallback(self, fb):
        self._config["fallback"] = fb
        return self

    def cache(self, ttl: float = None, maxsize: int = 256, instance=None):
        self._config["cache"] = instance or TranqCache(ttl=ttl, maxsize=maxsize)
        return self

    def observe(self, event_bus=None, telemetry=False, service: str = "tranq"):
        if event_bus is not None:
            self._config["event_bus"] = event_bus
        if telemetry:
            from .telemetry import Telemetry
            self._config["telemetry"] = Telemetry(service)
        return self

    def build(self) -> ResiliencePolicy:
        return ResiliencePolicy(dict(self._config))

    def __call__(self, func):
        return self.build()(func)


def resilient(**kwargs):
    """Shortcut decorator builder.

    @tranq.resilient(max_attempts=3, timeout=5)
    def f(): ...
    """
    builder = PolicyBuilder()
    if "max_attempts" in kwargs or "wait" in kwargs or "stop" in kwargs:
        builder.retry(
            max_attempts=kwargs.pop("max_attempts", 3),
            wait=kwargs.pop("wait", None),
            stop=kwargs.pop("stop", None),
            retry_if=kwargs.pop("retry_if", None),
        )
    if "timeout" in kwargs:
        builder.timeout(kwargs.pop("timeout"))
    if "circuit_breaker" in kwargs:
        builder.circuit_breaker(kwargs.pop("circuit_breaker"))
    if "fallback" in kwargs:
        builder.fallback(kwargs.pop("fallback"))
    if "cache_ttl" in kwargs:
        builder.cache(ttl=kwargs.pop("cache_ttl"))
    if "event_bus" in kwargs:
        builder.observe(event_bus=kwargs.pop("event_bus"))
    return builder
