import time
import functools
import asyncio
from typing import Callable, Union

_profiles = {}

def profile(func: Callable) -> Callable:
    """Decorator to measure execution time of a sync function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            dur = time.perf_counter() - start
            key = func.__name__
            if key not in _profiles:
                _profiles[key] = {"calls": 0, "total_duration": 0.0}
            _profiles[key]["calls"] += 1
            _profiles[key]["total_duration"] += dur
    return wrapper

def async_profile(func: Callable) -> Callable:
    """Decorator to measure execution time of an async function."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            dur = time.perf_counter() - start
            key = func.__name__
            if key not in _profiles:
                _profiles[key] = {"calls": 0, "total_duration": 0.0}
            _profiles[key]["calls"] += 1
            _profiles[key]["total_duration"] += dur
    return wrapper

def get_profile(name: str = None):
    if name:
        return _profiles.get(name, {})
    return dict(_profiles)
