import asyncio
import inspect
import logging
import time
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Type, Union
from .policies import Policy
from .utils import setup_logging, apply_jitter, compute_backoff
from .circuit_breaker import CircuitBreaker
from .async_circuit_breaker import AsyncCircuitBreaker
from .exceptions import CircuitBreakerError

_state_counter: ContextVar[Optional[Dict[str, int]]] = ContextVar("state_counter", default=None)

def _get_state_dict() -> Dict[str, int]:
    d = _state_counter.get()
    if d is None:
        d = {}
        _state_counter.set(d)
    return d

class RetryGroup:
    """All-or-nothing retry group for sync functions."""
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
        fallback: Optional[Callable] = None,
        reraise: bool = True,
        log_level: int = logging.ERROR,
        message: Optional[str] = None,
        retry_if: Optional[Callable[[BaseException], bool]] = None,
        on_error: Optional[Dict[Type[BaseException], Callable]] = None,
        circuit_breaker: Optional[Union[CircuitBreaker, AsyncCircuitBreaker]] = None,
        stateful: bool = False,
        reporters: Optional[List] = None,
        inject: Optional[Dict[str, Any]] = None,
    ):
        self.funcs = list(funcs)
        self.on = on if isinstance(on, tuple) else (on,)
        self.retry = retry
        self.delay = delay
        self.backoff = backoff
        self.backoff_strategy = backoff_strategy
        self.max_delay = max_delay
        self.jitter = jitter
        self.fallback = fallback
        self.reraise = reraise
        self.log_level = log_level
        self.message = message
        self.retry_if = retry_if
        self.on_error = on_error
        self.circuit_breaker = circuit_breaker
        self.stateful = stateful
        self.reporters = reporters if reporters is not None else []
        self.inject = inject if inject is not None else {}

    def run(self, *args, **kwargs):
        logger = setup_logging(level=self.log_level)
        attempts = self.retry + 1

        counter_key = "retry_group" if self.stateful else None
        state_dict = _get_state_dict() if counter_key else {}
        attempt_start = state_dict.get(counter_key, 0) if counter_key else 0

        injected = {**self.inject}
        for key, val in injected.items():
            if key not in kwargs:
                kwargs[key] = val

        cb = self.circuit_breaker
        is_async_cb = isinstance(cb, AsyncCircuitBreaker)
        if cb and not is_async_cb:
            if not cb.allow_request():
                if self.reraise:
                    raise CircuitBreakerError("Circuit breaker is open")
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                return None

        for attempt in range(attempt_start, attempts):
            try:
                results = []
                for func in self.funcs:
                    results.append(func(*args, **kwargs))
                if cb and not is_async_cb:
                    cb.record_success()
                if counter_key and counter_key in state_dict:
                    del state_dict[counter_key]
                    _state_counter.set(state_dict)
                return results
            except self.on as e:
                if self.on_error:
                    for exc_type, handler in self.on_error.items():
                        if isinstance(e, exc_type):
                            handler(e)
                            break

                should_retry = True
                if self.retry_if is not None:
                    should_retry = self.retry_if(e)

                if should_retry and attempt < attempts - 1:
                    log_msg = self.message.format(attempt=attempt+1) if self.message else f"Retry group error: {e} (attempt {attempt+1}/{attempts})"
                    logger.log(self.log_level, log_msg)
                    for rep in self.reporters:
                        rep.report(e, {"func": "retry_group", "attempt": attempt+1, "args": args, "kwargs": kwargs})
                    if cb and not is_async_cb:
                        cb.record_failure()
                    t = compute_backoff(attempt, self.delay, self.backoff, self.backoff_strategy, self.max_delay)
                    time.sleep(apply_jitter(t, self.jitter))
                    if counter_key:
                        state_dict[counter_key] = attempt + 1
                        _state_counter.set(state_dict)
                    continue
                else:
                    for rep in self.reporters:
                        rep.report(e, {"func": "retry_group", "attempt": attempt+1})
                    if cb and not is_async_cb:
                        cb.record_failure()
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.reraise:
                        raise
                    return None
        return None


class AsyncRetryGroup:
    """All-or-nothing retry group for async functions (supports mixed sync/async)."""
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
        fallback: Optional[Callable] = None,
        reraise: bool = True,
        log_level: int = logging.ERROR,
        message: Optional[str] = None,
        retry_if: Optional[Callable[[BaseException], bool]] = None,
        on_error: Optional[Dict[Type[BaseException], Callable]] = None,
        circuit_breaker: Optional[Union[CircuitBreaker, AsyncCircuitBreaker]] = None,
        stateful: bool = False,
        reporters: Optional[List] = None,
        inject: Optional[Dict[str, Any]] = None,
    ):
        self.funcs = list(funcs)
        self.on = on if isinstance(on, tuple) else (on,)
        self.retry = retry
        self.delay = delay
        self.backoff = backoff
        self.backoff_strategy = backoff_strategy
        self.max_delay = max_delay
        self.jitter = jitter
        self.fallback = fallback
        self.reraise = reraise
        self.log_level = log_level
        self.message = message
        self.retry_if = retry_if
        self.on_error = on_error
        self.circuit_breaker = circuit_breaker
        self.stateful = stateful
        self.reporters = reporters if reporters is not None else []
        self.inject = inject if inject is not None else {}

    async def run(self, *args, **kwargs):
        logger = setup_logging(level=self.log_level)
        attempts = self.retry + 1

        counter_key = "async_retry_group" if self.stateful else None
        state_dict = _get_state_dict() if counter_key else {}
        attempt_start = state_dict.get(counter_key, 0) if counter_key else 0

        injected = {**self.inject}
        for key, val in injected.items():
            if key not in kwargs:
                kwargs[key] = val

        cb = self.circuit_breaker
        is_async_cb = isinstance(cb, AsyncCircuitBreaker)
        if cb:
            if is_async_cb:
                if not await cb.allow_request():
                    if self.reraise:
                        raise CircuitBreakerError("Circuit breaker is open")
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    return None
            else:
                if not cb.allow_request():
                    if self.reraise:
                        raise CircuitBreakerError("Circuit breaker is open")
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    return None

        for attempt in range(attempt_start, attempts):
            try:
                results = []
                for func in self.funcs:
                    if inspect.iscoroutinefunction(func):
                        results.append(await func(*args, **kwargs))
                    else:
                        results.append(func(*args, **kwargs))
                if cb:
                    if is_async_cb:
                        await cb.record_success()
                    else:
                        cb.record_success()
                if counter_key and counter_key in state_dict:
                    del state_dict[counter_key]
                    _state_counter.set(state_dict)
                return results
            except self.on as e:
                if self.on_error:
                    for exc_type, handler in self.on_error.items():
                        if isinstance(e, exc_type):
                            handler(e)
                            break

                should_retry = True
                if self.retry_if is not None:
                    should_retry = self.retry_if(e)

                if should_retry and attempt < attempts - 1:
                    log_msg = self.message.format(attempt=attempt+1) if self.message else f"Retry group error: {e} (attempt {attempt+1}/{attempts})"
                    logger.log(self.log_level, log_msg)
                    for rep in self.reporters:
                        rep.report(e, {"func": "async_retry_group", "attempt": attempt+1})
                    if cb:
                        if is_async_cb:
                            await cb.record_failure()
                        else:
                            cb.record_failure()
                    t = compute_backoff(attempt, self.delay, self.backoff, self.backoff_strategy, self.max_delay)
                    await asyncio.sleep(apply_jitter(t, self.jitter))
                    if counter_key:
                        state_dict[counter_key] = attempt + 1
                        _state_counter.set(state_dict)
                    continue
                else:
                    for rep in self.reporters:
                        rep.report(e, {"func": "async_retry_group", "attempt": attempt+1})
                    if cb:
                        if is_async_cb:
                            await cb.record_failure()
                        else:
                            cb.record_failure()
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.reraise:
                        raise
                    return None
        return None


def retry_group(*funcs: Callable, **kwargs) -> RetryGroup:
    return RetryGroup(*funcs, **kwargs)

def async_retry_group(*funcs: Callable, **kwargs) -> AsyncRetryGroup:
    return AsyncRetryGroup(*funcs, **kwargs)