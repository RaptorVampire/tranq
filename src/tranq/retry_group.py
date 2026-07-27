import asyncio
import inspect
import logging
import time
from typing import Any, Callable, List, Optional, Type, Union
from .policies import Policy
from .utils import setup_logging, apply_jitter, compute_backoff

class RetryGroup:
    def __init__(
        self,
        *funcs: Callable,
        on: Union[Type[BaseException], tuple] = Exception,
        retry: int = 0,
        delay: float = 0.0,
        backoff: float = 1.0,
        backoff_strategy: str = "exponential",
        max_delay: Optional[float] = None,
        jitter: bool = False,
        reraise: bool = True,
        log_level: int = logging.ERROR,
        message: Optional[str] = None,
    ):
        self.funcs = list(funcs)
        self.on = on if isinstance(on, tuple) else (on,)
        self.retry = retry
        self.delay = delay
        self.backoff = backoff
        self.backoff_strategy = backoff_strategy
        self.max_delay = max_delay
        self.jitter = jitter
        self.reraise = reraise
        self.log_level = log_level
        self.message = message

    def run(self, *args, **kwargs):
        logger = setup_logging(level=self.log_level)
        attempts = self.retry + 1
        for attempt in range(attempts):
            try:
                results = []
                for func in self.funcs:
                    results.append(func(*args, **kwargs))
                return results
            except self.on as e:
                if attempt == attempts - 1:
                    if self.reraise:
                        raise
                    return None
                log_msg = self.message.format(attempt=attempt+1) if self.message else f"Retry group error: {e} (attempt {attempt+1}/{attempts})"
                logger.log(self.log_level, log_msg)
                t = compute_backoff(attempt, self.delay, self.backoff, self.backoff_strategy, self.max_delay)
                time.sleep(apply_jitter(t, self.jitter))
        return None

class AsyncRetryGroup:
    def __init__(
        self,
        *funcs: Callable,
        on: Union[Type[BaseException], tuple] = Exception,
        retry: int = 0,
        delay: float = 0.0,
        backoff: float = 1.0,
        backoff_strategy: str = "exponential",
        max_delay: Optional[float] = None,
        jitter: bool = False,
        reraise: bool = True,
        log_level: int = logging.ERROR,
        message: Optional[str] = None,
    ):
        self.funcs = list(funcs)
        self.on = on if isinstance(on, tuple) else (on,)
        self.retry = retry
        self.delay = delay
        self.backoff = backoff
        self.backoff_strategy = backoff_strategy
        self.max_delay = max_delay
        self.jitter = jitter
        self.reraise = reraise
        self.log_level = log_level
        self.message = message

    async def run(self, *args, **kwargs):
        logger = setup_logging(level=self.log_level)
        attempts = self.retry + 1
        for attempt in range(attempts):
            try:
                results = []
                for func in self.funcs:
                    if inspect.iscoroutinefunction(func):
                        results.append(await func(*args, **kwargs))
                    else:
                        results.append(func(*args, **kwargs))
                return results
            except self.on as e:
                if attempt == attempts - 1:
                    if self.reraise:
                        raise
                    return None
                log_msg = self.message.format(attempt=attempt+1) if self.message else f"Retry group error: {e} (attempt {attempt+1}/{attempts})"
                logger.log(self.log_level, log_msg)
                t = compute_backoff(attempt, self.delay, self.backoff, self.backoff_strategy, self.max_delay)
                await asyncio.sleep(apply_jitter(t, self.jitter))
        return None

def retry_group(*funcs: Callable, **kwargs) -> RetryGroup:
    return RetryGroup(*funcs, **kwargs)

def async_retry_group(*funcs: Callable, **kwargs) -> AsyncRetryGroup:
    return AsyncRetryGroup(*funcs, **kwargs)
