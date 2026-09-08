import asyncio
import logging
import random
from typing import Optional

try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_logging(level: int = logging.ERROR, fmt: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("tranq")
    if not logger.handlers:
        if RICH_AVAILABLE:
            console = Console(stderr=True)
            handler = RichHandler(console=console, rich_tracebacks=True, markup=True)
            formatter = logging.Formatter(fmt or "%(message)s")
            handler.setFormatter(formatter)
        else:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt or "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def apply_jitter(delay: float, jitter: bool) -> float:
    if jitter:
        return delay * (0.75 + 0.5 * random.random())
    return delay


def compute_backoff(attempt: int, delay: float, backoff: float, strategy, max_delay):
    if strategy == "exponential":
        t = delay * (backoff ** attempt)
    elif strategy == "linear":
        t = delay + delay * attempt
    elif strategy == "fibonacci":
        a, b = 1, 1
        for _ in range(attempt):
            a, b = b, a + b
        t = delay * a
    else:
        t = strategy(attempt)  # custom callable
    if max_delay is not None:
        t = min(t, max_delay)
    return t


def _call_hook(hook, *args) -> None:
    """Safely invoke a synchronous lifecycle hook; never raises."""
    if hook is None:
        return
    try:
        hook(*args)
    except Exception:
        pass


async def _acall_hook(hook, *args) -> None:
    """Safely invoke a sync or async lifecycle hook; never raises."""
    if hook is None:
        return
    try:
        res = hook(*args)
        if asyncio.iscoroutine(res):
            await res
    except Exception:
        pass


def run_with_timeout(func, args, kwargs, timeout: float):
    """Run a synchronous function with a timeout using a worker thread.

    Raises FunctionTimeoutError if the function does not return in time.
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutTimeout
    from .exceptions import FunctionTimeoutError

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except _FutTimeout:
            name = getattr(func, "__name__", "function")
            raise FunctionTimeoutError(f"{name} timed out after {timeout}s")
    finally:
        executor.shutdown(wait=False)
