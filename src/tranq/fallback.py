"""Fallback strategies: static, callable, async, chain, cached, conditional."""
import inspect


class FallbackChain:
    """Try a sequence of fallbacks in order; return the first that succeeds.

    Each item may be a value or a callable. Callables are invoked with the
    original arguments. The chain can mix sync and async callables when used
    from an async context via ``run_async``.
    """

    def __init__(self, *fallbacks):
        self.fallbacks = list(fallbacks)

    def run(self, *args, **kwargs):
        last = None
        for fb in self.fallbacks:
            try:
                if callable(fb):
                    return fb(*args, **kwargs)
                return fb
            except Exception as e:
                last = e
        if last is not None:
            raise last
        return None

    async def run_async(self, *args, **kwargs):
        last = None
        for fb in self.fallbacks:
            try:
                if inspect.iscoroutinefunction(fb):
                    return await fb(*args, **kwargs)
                if callable(fb):
                    return fb(*args, **kwargs)
                return fb
            except Exception as e:
                last = e
        if last is not None:
            raise last
        return None


class CachedFallback:
    """Fallback that serves the last successful result (stale-while-failing)."""

    def __init__(self, default=None):
        self.default = default
        self._last = default
        self._has = False

    def remember(self, value):
        self._last = value
        self._has = True

    def __call__(self, *args, **kwargs):
        return self._last if self._has else self.default


class ConditionalFallback:
    """Choose a fallback based on the exception that occurred."""

    def __init__(self):
        self._rules = []

    def when(self, exception_type, fallback):
        self._rules.append((exception_type, fallback))
        return self

    def resolve(self, exception, *args, **kwargs):
        for exc_type, fb in self._rules:
            if isinstance(exception, exc_type):
                return fb(*args, **kwargs) if callable(fb) else fb
        return None
