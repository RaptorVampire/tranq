"""LLM API resilience: rate limits, Retry-After, provider/model fallback."""
import inspect
import functools

from . import presets as _presets
from .fallback import FallbackChain


def llm(max_attempts: int = 5, timeout: float = 60.0, providers=None):
    """Decorator for LLM API calls with rate-limit handling and provider fallback.

    ``providers`` is an optional ordered list of callables; when the primary
    fails, each provider is tried in sequence (automatic provider failover).
    """
    preset = _presets.llm()
    wait = preset["wait"]
    stop = preset["stop"]
    retry_if = preset["retry_if"]

    def decorator(func):
        chain = FallbackChain(*(providers or [])) if providers else None

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def aw(*args, **kwargs):
                import time as _t
                import asyncio as _aio
                attempt = 0
                start = _t.monotonic()
                last = None
                while True:
                    attempt += 1
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last = e
                        elapsed = _t.monotonic() - start
                        should = True
                        if retry_if is not None:
                            should = retry_if(e)
                        if stop(attempt, elapsed) or not should:
                            break
                        _aio.sleep(wait(attempt))
                if chain is not None:
                    return await chain.run_async(*args, **kwargs)
                raise last
            return aw
        else:
            @functools.wraps(func)
            def w(*args, **kwargs):
                import time as _t
                attempt = 0
                start = _t.monotonic()
                last = None
                while True:
                    attempt += 1
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last = e
                        elapsed = _t.monotonic() - start
                        should = True
                        if retry_if is not None:
                            should = retry_if(e)
                        if stop(attempt, elapsed) or not should:
                            break
                        _t.sleep(wait(attempt))
                if chain is not None:
                    return chain.run(*args, **kwargs)
                raise last
            return w
    return decorator
