"""tranq.auto(): inspect runtime behavior and recommend/apply a policy."""
import time
import functools
import inspect

from . import presets as _presets


def _detect(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ("http", "request", "get", "post", "fetch", "api")):
        return "http"
    if any(k in n for k in ("db", "sql", "query", "database")):
        return "database"
    if "redis" in n or "cache" in n:
        return "redis"
    if any(k in n for k in ("kafka", "queue", "publish", "consume")):
        return "kafka"
    if any(k in n for k in ("llm", "gpt", "model", "completion", "chat")):
        return "llm"
    return "http"


def recommend_policy(func) -> dict:
    """Recommend a policy config based on the function name/behavior."""
    kind = _detect(getattr(func, "__name__", ""))
    preset_map = {
        "http": _presets.http,
        "database": _presets.database,
        "redis": _presets.redis,
        "kafka": _presets.kafka,
        "llm": _presets.llm,
    }
    factory = preset_map.get(kind, _presets.http)
    cfg = factory()
    cfg["detected_kind"] = kind
    return cfg


def auto(apply: bool = False, verbose: bool = False):
    """Decorator that detects the operation type and applies a recommended policy.

    By default ``apply=False``: tranq only RECOMMENDS (prints) the policy and
    runs the function unchanged, so it never silently changes behavior. Set
    ``apply=True`` to actually wrap with the recommended retry/timeout policy.
    """
    def decorator(func):
        cfg = recommend_policy(func)
        if verbose:
            print(f"[tranq.auto] detected={cfg['detected_kind']} "
                  f"timeout={cfg.get('timeout')} stop={cfg.get('stop')}")

        if not apply:
            return func

        wait = cfg["wait"]
        stop = cfg["stop"]
        retry_if = cfg.get("retry_if")
        timeout = cfg.get("timeout")

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def aw(*args, **kwargs):
                import asyncio as _aio
                attempt = 0
                start = time.monotonic()
                last = None
                while True:
                    attempt += 1
                    try:
                        if timeout:
                            return await _aio.wait_for(func(*args, **kwargs), timeout)
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last = e
                        elapsed = time.monotonic() - start
                        should = retry_if(e) if retry_if is not None else True
                        if stop(attempt, elapsed) or not should:
                            break
                        await _aio.sleep(wait(attempt))
                raise last
            return aw
        else:
            @functools.wraps(func)
            def w(*args, **kwargs):
                attempt = 0
                start = time.monotonic()
                last = None
                while True:
                    attempt += 1
                    try:
                        if timeout:
                            from .utils import run_with_timeout
                            return run_with_timeout(func, args, kwargs, timeout)
                        return func(*args, **kwargs)
                    except Exception as e:
                        last = e
                        elapsed = time.monotonic() - start
                        should = retry_if(e) if retry_if is not None else True
                        if stop(attempt, elapsed) or not should:
                            break
                        time.sleep(wait(attempt))
                raise last
            return w
    return decorator
