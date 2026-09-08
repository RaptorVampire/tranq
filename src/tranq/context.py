import asyncio
import inspect
import logging
import time
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from .policies import Policy
from .decorators import _merge_policy, _is_async_cb
from .utils import (setup_logging, apply_jitter, compute_backoff,
                    _call_hook, _acall_hook, run_with_timeout)
from .circuit_breaker import CircuitBreaker
from .async_circuit_breaker import AsyncCircuitBreaker
from .exceptions import CircuitBreakerError, ResultNotAcceptedError, FunctionTimeoutError
from .metrics import record_metric

_state_counter = ContextVar("state_counter", default=None)

ExcSpec = Union[Type[BaseException], Tuple[Type[BaseException], ...]]


def _get_state_dict():
    d = _state_counter.get()
    if d is None:
        d = {}
        _state_counter.set(d)
    return d


class RetryContext:
    """Context manager offering all retry/decorator features (sync)."""

    def __init__(self, on: ExcSpec = Exception, retry: int = 0, delay: float = 0.0,
                 backoff: float = 1.0, backoff_strategy: str = "exponential",
                 max_delay: Optional[float] = None, jitter: bool = False,
                 fallback: Optional[Callable] = None, reraise: bool = True,
                 log_level: int = logging.ERROR, message: Optional[str] = None,
                 policy: Optional[Policy] = None, retry_if=None, retry_on_result=None,
                 on_error=None, metrics: bool = False, metric_prefix: str = "",
                 circuit_breaker=None, stateful: bool = False, reporters: Optional[List] = None,
                 inject: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                 on_retry=None, on_success=None, on_failure=None, on_complete=None,
                 retry_budget=None):
        merged = _merge_policy(
            policy, retry, delay, backoff, jitter, reraise, log_level, message,
            retry_if, retry_on_result, on_error, metrics, metric_prefix,
            circuit_breaker, stateful, backoff_strategy, max_delay, reporters,
            0, inject, timeout, on_retry, on_success, on_failure, on_complete,
            retry_budget
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

        if self.policy.retry_budget is not None:
            self.policy.retry_budget.record_call()

        cb = self.policy.circuit_breaker
        is_async = _is_async_cb(cb)
        start_time = time.perf_counter()

        if cb and not is_async:
            if not cb.allow_request():
                if self.policy.reraise:
                    raise CircuitBreakerError("Circuit breaker is open")
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                return None

        for attempt in range(attempt_start, attempts):
            try:
                if self.policy.timeout is not None:
                    result = run_with_timeout(func, args, kwargs, self.policy.timeout)
                else:
                    result = func(*args, **kwargs)
            except self.on as e:
                if self.policy.metrics:
                    record_metric(self.policy.metric_prefix, func.__name__, 0, True)

                # on_error handlers: run the matching callback, then stop retrying.
                handled = False
                if self.policy.on_error:
                    for exc_type, handler in self.policy.on_error.items():
                        if isinstance(e, exc_type):
                            handler(e)
                            handled = True
                            break

                if handled:
                    if cb and not is_async:
                        cb.record_failure()
                    _call_hook(self.policy.on_failure, e)
                    _call_hook(self.policy.on_complete)
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.policy.reraise:
                        raise
                    return None

                should_retry = True
                if self.policy.retry_if is not None:
                    should_retry = self.policy.retry_if(e)
                if self.policy.retry_budget is not None and not self.policy.retry_budget.allow_retry():
                    should_retry = False

                if should_retry and attempt < attempts - 1:
                    _call_hook(self.policy.on_retry, e, attempt + 1)
                    logger.log(self.policy.log_level,
                               f"Error in {func.__name__}: {e} (attempt {attempt + 1}/{attempts})")
                    for rep in self.policy.reporters:
                        rep.report(e, {"func": func.__name__, "attempt": attempt + 1})
                    if cb and not is_async:
                        cb.record_failure()
                    t = compute_backoff(attempt, self.delay, self.policy.backoff,
                                        self.backoff_strategy, self.max_delay)
                    time.sleep(apply_jitter(t, self.policy.jitter))
                    if counter_key:
                        state_dict[counter_key] = attempt + 1
                        _state_counter.set(state_dict)
                    continue
                else:
                    for rep in self.policy.reporters:
                        rep.report(e, {"func": func.__name__, "attempt": attempt + 1})
                    if cb and not is_async:
                        cb.record_failure()
                    _call_hook(self.policy.on_failure, e)
                    _call_hook(self.policy.on_complete)
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.policy.reraise:
                        raise
                    return None
            else:
                if self.policy.retry_on_result and self.policy.retry_on_result(result):
                    if attempt < attempts - 1:
                        logger.log(self.policy.log_level,
                                   f"Result not accepted in {func.__name__} (attempt {attempt + 1}/{attempts})")
                        t = compute_backoff(attempt, self.delay, self.policy.backoff,
                                            self.backoff_strategy, self.max_delay)
                        time.sleep(apply_jitter(t, self.policy.jitter))
                        continue
                    else:
                        _call_hook(self.policy.on_failure, ResultNotAcceptedError(str(result)))
                        _call_hook(self.policy.on_complete)
                        if self.policy.reraise:
                            raise ResultNotAcceptedError(f"Result not accepted: {result}")
                        return result if self.fallback is None else self.fallback(*args, **kwargs)

                # success
                elapsed = time.perf_counter() - start_time
                if self.policy.metrics:
                    record_metric(self.policy.metric_prefix, func.__name__, elapsed, False)
                if cb and not is_async:
                    cb.record_success()
                if counter_key and counter_key in state_dict:
                    del state_dict[counter_key]
                    _state_counter.set(state_dict)
                _call_hook(self.policy.on_success, result)
                _call_hook(self.policy.on_complete)
                return result

        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def retry(on: ExcSpec = Exception, retry: int = 0, delay: float = 0.0, backoff: float = 1.0,
          backoff_strategy: str = "exponential", max_delay: Optional[float] = None,
          jitter: bool = False, fallback: Optional[Callable] = None, reraise: bool = True,
          log_level: int = logging.ERROR, message: Optional[str] = None,
          policy: Optional[Policy] = None, retry_if=None, retry_on_result=None,
          on_error=None, metrics: bool = False, metric_prefix: str = "",
          circuit_breaker=None, stateful: bool = False, reporters: Optional[List] = None,
          inject: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
          on_retry=None, on_success=None, on_failure=None, on_complete=None,
          retry_budget=None) -> RetryContext:
    return RetryContext(
        on=on, retry=retry, delay=delay, backoff=backoff,
        backoff_strategy=backoff_strategy, max_delay=max_delay, jitter=jitter,
        fallback=fallback, reraise=reraise, log_level=log_level, message=message,
        policy=policy, retry_if=retry_if, retry_on_result=retry_on_result,
        on_error=on_error, metrics=metrics, metric_prefix=metric_prefix,
        circuit_breaker=circuit_breaker, stateful=stateful, reporters=reporters,
        inject=inject, timeout=timeout, on_retry=on_retry, on_success=on_success,
        on_failure=on_failure, on_complete=on_complete, retry_budget=retry_budget,
    )


class AsyncRetryContext:
    """Async context manager offering all retry/decorator features."""

    def __init__(self, **kwargs):
        self.on = kwargs.get("on", Exception)
        self.on = self.on if isinstance(self.on, tuple) else (self.on,)
        self.policy = _merge_policy(
            kwargs.get("policy"), kwargs.get("retry", 0), kwargs.get("delay", 0.0),
            kwargs.get("backoff", 1.0), kwargs.get("jitter", False),
            kwargs.get("reraise", True), kwargs.get("log_level", logging.ERROR),
            kwargs.get("message"), kwargs.get("retry_if"), kwargs.get("retry_on_result"),
            kwargs.get("on_error"), kwargs.get("metrics", False),
            kwargs.get("metric_prefix", ""), kwargs.get("circuit_breaker"),
            kwargs.get("stateful", False), kwargs.get("backoff_strategy", "exponential"),
            kwargs.get("max_delay"), kwargs.get("reporters"), 0, kwargs.get("inject"),
            kwargs.get("timeout"), kwargs.get("on_retry"), kwargs.get("on_success"),
            kwargs.get("on_failure"), kwargs.get("on_complete"), kwargs.get("retry_budget"),
        )
        self.fallback = kwargs.get("fallback")
        self.backoff_strategy = kwargs.get("backoff_strategy", "exponential")
        self.max_delay = kwargs.get("max_delay")
        self.delay = kwargs.get("delay", 0.0)

    async def run(self, func, *args, **kwargs):
        logger = setup_logging(level=self.policy.log_level, fmt=self.policy.log_format)
        attempts = self.policy.retry + 1

        for key, val in self.policy.inject.items():
            if key not in kwargs:
                kwargs[key] = val

        if self.policy.retry_budget is not None:
            self.policy.retry_budget.record_call()

        cb = self.policy.circuit_breaker
        is_async = _is_async_cb(cb)
        start_time = time.perf_counter()

        if cb:
            allowed = await cb.allow_request() if is_async else cb.allow_request()
            if not allowed:
                if self.policy.reraise:
                    raise CircuitBreakerError("Circuit breaker is open")
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                return None

        for attempt in range(attempts):
            try:
                if self.policy.timeout is not None:
                    try:
                        result = await asyncio.wait_for(func(*args, **kwargs), self.policy.timeout)
                    except asyncio.TimeoutError:
                        raise FunctionTimeoutError(
                            f"{func.__name__} timed out after {self.policy.timeout}s")
                else:
                    result = await func(*args, **kwargs)
            except self.on as e:
                if self.policy.metrics:
                    record_metric(self.policy.metric_prefix, func.__name__, 0, True)

                # on_error handlers: run the matching callback, then stop retrying.
                handled = False
                if self.policy.on_error:
                    for exc_type, handler in self.policy.on_error.items():
                        if isinstance(e, exc_type):
                            res = handler(e)
                            if asyncio.iscoroutine(res):
                                await res
                            handled = True
                            break

                if handled:
                    if cb:
                        if is_async:
                            await cb.record_failure()
                        else:
                            cb.record_failure()
                    await _acall_hook(self.policy.on_failure, e)
                    await _acall_hook(self.policy.on_complete)
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.policy.reraise:
                        raise
                    return None

                should_retry = True
                if self.policy.retry_if is not None:
                    should_retry = self.policy.retry_if(e)
                if self.policy.retry_budget is not None and not self.policy.retry_budget.allow_retry():
                    should_retry = False

                if should_retry and attempt < attempts - 1:
                    await _acall_hook(self.policy.on_retry, e, attempt + 1)
                    logger.log(self.policy.log_level,
                               f"Error in {func.__name__}: {e} (attempt {attempt + 1}/{attempts})")
                    for rep in self.policy.reporters:
                        rep.report(e, {"func": func.__name__, "attempt": attempt + 1})
                    if cb:
                        if is_async:
                            await cb.record_failure()
                        else:
                            cb.record_failure()
                    t = compute_backoff(attempt, self.delay, self.policy.backoff,
                                        self.backoff_strategy, self.max_delay)
                    await asyncio.sleep(apply_jitter(t, self.policy.jitter))
                    continue
                else:
                    for rep in self.policy.reporters:
                        rep.report(e, {"func": func.__name__, "attempt": attempt + 1})
                    if cb:
                        if is_async:
                            await cb.record_failure()
                        else:
                            cb.record_failure()
                    await _acall_hook(self.policy.on_failure, e)
                    await _acall_hook(self.policy.on_complete)
                    if self.fallback:
                        return self.fallback(*args, **kwargs)
                    if self.policy.reraise:
                        raise
                    return None
            else:
                if self.policy.retry_on_result and self.policy.retry_on_result(result):
                    if attempt < attempts - 1:
                        logger.log(self.policy.log_level,
                                   f"Result not accepted in {func.__name__} (attempt {attempt + 1}/{attempts})")
                        t = compute_backoff(attempt, self.delay, self.policy.backoff,
                                            self.backoff_strategy, self.max_delay)
                        await asyncio.sleep(apply_jitter(t, self.policy.jitter))
                        continue
                    else:
                        await _acall_hook(self.policy.on_failure, ResultNotAcceptedError(str(result)))
                        await _acall_hook(self.policy.on_complete)
                        if self.policy.reraise:
                            raise ResultNotAcceptedError(f"Result not accepted: {result}")
                        return result if self.fallback is None else self.fallback(*args, **kwargs)

                elapsed = time.perf_counter() - start_time
                if self.policy.metrics:
                    record_metric(self.policy.metric_prefix, func.__name__, elapsed, False)
                if cb:
                    if is_async:
                        await cb.record_success()
                    else:
                        cb.record_success()
                await _acall_hook(self.policy.on_success, result)
                await _acall_hook(self.policy.on_complete)
                return result

        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def retry_async(**kwargs) -> AsyncRetryContext:
    """Create an async retry context.

    Usage::

        async with retry_async(on=ValueError, retry=3) as ctx:
            result = await ctx.run(my_async_func, arg)
    """
    return AsyncRetryContext(**kwargs)
