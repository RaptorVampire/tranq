import logging
import math
import random
import time
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
            formatter = logging.Formatter(fmt or "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger

def apply_jitter(delay: float, jitter: bool) -> float:
    if jitter:
        return delay * (0.75 + 0.5 * random.random())
    return delay

def compute_backoff(attempt: int, delay: float, backoff: float, strategy: str, max_delay: Optional[float]) -> float:
    if strategy == "exponential":
        t = delay * (backoff ** attempt)
    elif strategy == "linear":
        t = delay + delay * attempt
    elif strategy == "fibonacci":
        if attempt == 0:
            t = delay
        else:
            a, b = 0, 1
            for _ in range(attempt + 1):
                a, b = b, a + b
            t = delay * a
    else:
        t = strategy(attempt)
    if max_delay is not None:
        t = min(t, max_delay)
    return t
