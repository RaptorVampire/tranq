import asyncio
import inspect
import functools
import threading

from .exceptions import BulkheadFullError


class Bulkhead:
    """Concurrency limiter for synchronous code (threading semaphore)."""

    def __init__(self, max_concurrent: int, timeout: float = None):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._sem = threading.Semaphore(max_concurrent)
        self._active = 0
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        ok = self._sem.acquire(timeout=self.timeout if self.timeout is not None else -1)
        if ok:
            with self._lock:
                self._active += 1
        return ok

    def release(self) -> None:
        with self._lock:
            self._active -= 1
        self._sem.release()

    @property
    def active(self) -> int:
        with self._lock:
            return self._active


class AsyncBulkhead:
    """Concurrency limiter for asynchronous code (asyncio semaphore)."""

    def __init__(self, max_concurrent: int, timeout: float = None):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._sem = asyncio.Semaphore(max_concurrent)
        self._active = 0

    async def acquire(self) -> bool:
        try:
            if self.timeout is None:
                await self._sem.acquire()
            elif self.timeout <= 0:
                # Non-blocking: succeed only if a slot is free right now.
                if self._sem.locked():
                    return False
                await self._sem.acquire()
            else:
                await asyncio.wait_for(self._sem.acquire(), self.timeout)
            self._active += 1
            return True
        except asyncio.TimeoutError:
            return False

    def release(self) -> None:
        self._active -= 1
        self._sem.release()

    @property
    def active(self) -> int:
        return self._active


def bulkhead(max_concurrent: int, timeout: float = None, raise_on_full: bool = True):
    """Decorator limiting how many calls may run concurrently."""

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            bh = AsyncBulkhead(max_concurrent, timeout)

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not await bh.acquire():
                    if raise_on_full:
                        raise BulkheadFullError(f"Bulkhead full for {func.__name__}")
                    return None
                try:
                    return await func(*args, **kwargs)
                finally:
                    bh.release()

            async_wrapper.bulkhead = bh
            return async_wrapper
        else:
            bh = Bulkhead(max_concurrent, timeout)

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not bh.acquire():
                    if raise_on_full:
                        raise BulkheadFullError(f"Bulkhead full for {func.__name__}")
                    return None
                try:
                    return func(*args, **kwargs)
                finally:
                    bh.release()

            sync_wrapper.bulkhead = bh
            return sync_wrapper

    return decorator
