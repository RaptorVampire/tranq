import logging
import time
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .policies import Policy
from .decorators import _merge_policy
from .utils import setup_logging, apply_jitter, compute_backoff
from .circuit_breaker import CircuitBreaker
from .async_circuit_breaker import AsyncCircuitBreaker
from .exceptions import CircuitBreakerError
from .metrics import record_metric

_state_counter: ContextVar[Optional[Dict[str, int]]] = ContextVar("state_counter", default=None)

def _get_state_dict() -> Dict[str, int]:
    d = _state_counter.get()
    if d is None:
        d = {}
        _state_counter.set(d)
    return d

class RetryContext:
    """Context manager offering all retry/decorator features."""
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
        retry_if: Optional[Callable[[BaseException], bool]] = None,
        retry_on_result: Optional[Callable[[Any], bool]] = None,
        on_error: Optional[Dict[Type[BaseException], Callable]] = None,
        metrics: bool = False,
        metric_prefix: str = "",
        circuit_breaker: Optional[Union[CircuitBreaker, AsyncCircuitBreaker]] = None,
        stateful: bool = False,
        reporters: Optional[List] = None,
        inject: Optional[Dict[str, Any]] = None,
    ):
        merged = _merge_policy(
            policy, retry, delay, backoff, jitter, reraise, log_level, message,
            retry_if, retry_on_result, on_error, metrics, metric_prefix,
            circuit_breaker, stateful, backoff_strategy, max_delay, reporters,
            0, inject
        )
        self.policy = merged
        self.on = on if isinstance(on, tuple) else (on,)
        self.fallback = fallback
        self.backoff_strategy = backoff_strategy
        self.max_delay = max_delay
        self.delay = delay

    def run(self, func, *args, **kwargs):
        logger = setup_logging(level=self.policy.log_level, fmt=self.policy.log_format)
        attempts = self.policy.retry + 1

        counter_key = f"{func.__module__}.{func.__name__}" if self.policy.stateful else None
        state_dict = _get_state_dict() if counter_key else {}
        attempt_start = state_dict.get(counter_key, 0) if counter_key else 0

        for key, val in self.policy.inject.items():
            if key not in kwargs:
                kwargs[key] = val

        cb = self.policy.circuit_breaker
        is_async_cb = isinstance(cb, AsyncCircuitBreaker)

        start_time = time.perf_counter()

        if cb and not is_async_cb:
            if not cb.allow_request():
                if self.policy.reraise:
                    raise CircuitBreakerError("Circuit breaker is open")
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                return None

        for attempt in range(attempt_start, attempts):
            try:
                result = func(*args, **kwargs)
            except self.on as e:
                if self.policy.metrics:
                    record_metric(self.policy.metric_prefix, func.__name__, 0, True)

                if self.policy.on_error:
                    for exc_type, handler in self.policy.on_error.items():
                        if isinstance(e, exc_type):
                            handler(e)
                            break

                should_retry = True
                if self.policy.retry_if is not None:
                    should_retry = self.policy.retry_if(e)

                if should_retry and attempt < attempts - 1:
                    log_msg = self.policy.log_format.format(
                        func=func.__name__, error=e, attempt=attempt+1
                    ) if self.policy.log_format else f"Error in {func.__name__}: {e} (attempt {attempt+1}/{attempts})"
                    logger.log(self.policy.log_level, log_msg)

                    for rep in self.policy.reporters:
                        rep.report(e, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})

                    if cb and not is_async_cb:
                        cb.record_failure()

                    t = compute_backoff(attempt, self.delay, self.policy.backoff, self.backoff_strategy, self.max_delay)
                    time.sleep(apply_jitter(t, self.policy.jitter))

                    if counter_key:
                        state_dict[counter_key] = attempt + 1
                        _state_counter.set(state_dict)
                    continue
                else:
                    for rep in self.policy.reporters:
                        rep.report(e, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})
                    if cb and not is_async_cb:
                        cb.record_failure()
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.policy.reraise:
                        raise
                    return None
            else:
                if self.policy.retry_on_result and self.policy.retry_on_result(result):
                    if attempt < attempts - 1:
                        logger.log(self.policy.log_level, f"Result not accepted in {func.__name__} (attempt {attempt+1}/{attempts})")
                        for rep in self.policy.reporters:
                            rep.report(ValueError(f"Result not accepted: {result}"), {"func": func.__name__, "attempt": attempt+1})
                        t = compute_backoff(attempt, self.delay, self.policy.backoff, self.backoff_strategy, self.max_delay)
                        time.sleep(apply_jitter(t, self.policy.jitter))
                        continue
                    else:
                        if self.policy.reraise:
                            from .exceptions import ResultNotAcceptedError
                            raise ResultNotAcceptedError(f"Result not accepted: {result}")
                        return result if self.fallback is None else self.fallback(*args, **kwargs)

                elapsed = time.perf_counter() - start_time
                if self.policy.metrics:
                    record_metric(self.policy.metric_prefix, func.__name__, elapsed, False)

                if cb and not is_async_cb:
                    cb.record_success()
                if counter_key and counter_key in state_dict:
                    del state_dict[counter_key]
                    _state_counter.set(state_dict)
                return result
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
    retry_if: Optional[Callable[[BaseException], bool]] = None,
    retry_on_result: Optional[Callable[[Any], bool]] = None,
    on_error: Optional[Dict[Type[BaseException], Callable]] = None,
    metrics: bool = False,
    metric_prefix: str = "",
    circuit_breaker: Optional[Union[CircuitBreaker, AsyncCircuitBreaker]] = None,
    stateful: bool = False,
    reporters: Optional[List] = None,
    inject: Optional[Dict[str, Any]] = None,
) -> RetryContext:
    return RetryContext(
        on=on, retry=retry, delay=delay, backoff=backoff,
        backoff_strategy=backoff_strategy, max_delay=max_delay, jitter=jitter,
        fallback=fallback, reraise=reraise, log_level=log_level, message=message,
        policy=policy, retry_if=retry_if, retry_on_result=retry_on_result,
        on_error=on_error, metrics=metrics, metric_prefix=metric_prefix,
        circuit_breaker=circuit_breaker, stateful=stateful, reporters=reporters,
        inject=inject,
    )