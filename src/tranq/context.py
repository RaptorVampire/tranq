import logging
import time
from typing import Any, Callable, Optional, Type, Union
from .policies import Policy
from .decorators import _merge_policy
from .utils import setup_logging, apply_jitter, compute_backoff

class RetryContext:
    def __init__(
        self,
        on: Union[Type[BaseException], tuple] = Exception,
        retry: int = 0,
        delay: float = 0.0,
        backoff: float = 1.0,
        backoff_strategy: str = "exponential",
        max_delay: Optional[float] = None,
        jitter: bool = False,
        fallback: Optional[Callable] = None,
        reraise: bool = True,
        log_level: int = logging.ERROR,
        message: Optional[str] = None,
        policy: Optional[Policy] = None,
    ):
        merged = _merge_policy(policy, retry, delay, backoff, jitter, reraise, log_level, message)
        self.policy = merged
        self.on = on if isinstance(on, tuple) else (on,)
        self.fallback = fallback
        self.backoff_strategy = backoff_strategy
        self.max_delay = max_delay
        self.delay = delay

    def run(self, func, *args, **kwargs):
        logger = setup_logging(level=self.policy.log_level, fmt=self.policy.log_format)
        attempts = self.policy.retry + 1
        for attempt in range(attempts):
            try:
                return func(*args, **kwargs)
            except self.on as e:
                if attempt == attempts - 1:
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.policy.reraise:
                        raise
                    return None
                log_msg = self.policy.log_format.format(func=func.__name__, error=e, attempt=attempt+1) if self.policy.log_format else f"Error in {func.__name__}: {e} (attempt {attempt+1}/{attempts})"
                logger.log(self.policy.log_level, log_msg)
                t = compute_backoff(attempt, self.delay, self.policy.backoff, self.backoff_strategy, self.max_delay)
                time.sleep(apply_jitter(t, self.policy.jitter))
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def retry(
    on: Union[Type[BaseException], tuple] = Exception,
    retry: int = 0,
    delay: float = 0.0,
    backoff: float = 1.0,
    backoff_strategy: str = "exponential",
    max_delay: Optional[float] = None,
    jitter: bool = False,
    fallback: Optional[Callable] = None,
    reraise: bool = True,
    log_level: int = logging.ERROR,
    message: Optional[str] = None,
    policy: Optional[Policy] = None,
) -> RetryContext:
    return RetryContext(
        on=on, retry=retry, delay=delay, backoff=backoff,
        backoff_strategy=backoff_strategy, max_delay=max_delay, jitter=jitter,
        fallback=fallback, reraise=reraise, log_level=log_level, message=message, policy=policy,
    )
