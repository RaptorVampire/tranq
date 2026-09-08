import asyncio
import functools


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


def hedged(hedge_delay: float = 0.1, max_hedges: int = 2):
    """Decorator applying hedged requests to an async function."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await hedged_call(func, args=args, kwargs=kwargs,
                                     hedge_delay=hedge_delay, max_hedges=max_hedges)
        return wrapper

    return decorator
