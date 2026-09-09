"""Hedged requests: first-success, fastest-N, quorum and percentile-based delay."""
import asyncio
import functools
import time


async def hedged_call(func, args=(), kwargs=None, *, hedge_delay: float = 0.1,
                      max_hedges: int = 2):
    """Issue a request and, if it does not finish in time, launch hedges.

    Returns the first successful result and cancels the remaining in-flight
    attempts. If every attempt fails, re-raises the last observed exception.
    """
    kwargs = kwargs or {}
    exceptions = []
    tasks = set()
    max_attempts = max_hedges + 1

    async def _wrap():
        return await func(*args, **kwargs)

    tasks.add(asyncio.create_task(_wrap()))
    launched = 1

    while tasks:
        wait_timeout = hedge_delay if launched < max_attempts else None
        done, _ = await asyncio.wait(tasks, timeout=wait_timeout,
                                     return_when=asyncio.FIRST_COMPLETED)

        if not done:
            if launched < max_attempts:
                tasks.add(asyncio.create_task(_wrap()))
                launched += 1
            continue

        result_found = False
        result_value = None
        for d in done:
            tasks.discard(d)
            exc = d.exception()
            if exc is None:
                if not result_found:
                    result_found = True
                    result_value = d.result()
            else:
                exceptions.append(exc)

        if result_found:
            for t in list(tasks):
                t.cancel()
            return result_value

        if launched < max_attempts:
            tasks.add(asyncio.create_task(_wrap()))
            launched += 1

    if exceptions:
        raise exceptions[-1]
    raise RuntimeError("hedged call produced no result")


async def hedged_quorum(func, args=(), kwargs=None, *, quorum: int = 2,
                        max_attempts: int = 3, timeout: float = None):
    """Launch attempts and return once ``quorum`` of them succeed.

    Returns a list of the first ``quorum`` successful results.
    """
    kwargs = kwargs or {}

    async def _wrap():
        return await func(*args, **kwargs)

    tasks = [asyncio.create_task(_wrap()) for _ in range(max_attempts)]
    results = []
    exceptions = []
    pending = set(tasks)

    while pending and len(results) < quorum:
        done, pending = await asyncio.wait(pending, timeout=timeout,
                                           return_when=asyncio.FIRST_COMPLETED)
        if not done:
            break
        for d in done:
            exc = d.exception()
            if exc is None:
                results.append(d.result())
            else:
                exceptions.append(exc)

    for t in pending:
        t.cancel()

    if len(results) >= quorum:
        return results[:quorum]
    if exceptions:
        raise exceptions[-1]
    raise RuntimeError("quorum not reached")


class PercentileHedgeDelay:
    """Adaptive hedge delay based on a latency percentile of past calls."""

    def __init__(self, percentile: float = 0.95, window: int = 100):
        self.percentile = percentile
        self.window = window
        self._latencies = []

    def record(self, latency: float):
        self._latencies.append(latency)
        if len(self._latencies) > self.window:
            self._latencies.pop(0)

    def delay(self) -> float:
        if not self._latencies:
            return 0.1
        s = sorted(self._latencies)
        idx = min(len(s) - 1, int(self.percentile * len(s)))
        return s[idx]


def hedged(hedge_delay: float = 0.1, max_hedges: int = 2):
    """Decorator applying hedged requests to an async function."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await hedged_call(func, args=args, kwargs=kwargs,
                                     hedge_delay=hedge_delay, max_hedges=max_hedges)
        return wrapper

    return decorator
