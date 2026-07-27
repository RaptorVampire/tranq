import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .exceptions import TranqError, CircuitBreakerError, ResultNotAcceptedError
from .policies import Policy, get_global_policy
from .utils import setup_logging, apply_jitter, compute_backoff
from .circuit_breaker import CircuitBreaker
from .async_circuit_breaker import AsyncCircuitBreaker
from .metrics import record_metric

def _merge_policy(
    policy: Optional[Policy],
    retry: int,
    delay: float,
    backoff: float,
    jitter: bool,
    reraise: bool,
    log_level: int,
    message: Optional[str],
    retry_if: Optional[Callable[[BaseException], bool]] = None,
    retry_on_result: Optional[Callable[[Any], bool]] = None,
    on_error: Optional[Dict[Type[BaseException], Callable]] = None,
    metrics: bool = False,
    metric_prefix: str = "",
    circuit_breaker: Optional[Union[CircuitBreaker, AsyncCircuitBreaker]] = None,
    stateful: bool = False,
    backoff_strategy: Optional[str] = None,
    max_delay: Optional[float] = None,
    reporters: Optional[List] = None,
    priority: int = 0,
    inject: Optional[Dict[str, Any]] = None,
) -> Policy:
    if policy is None:
        policy = get_global_policy()
    d = policy.__dict__.copy()
    if retry != 0: d["retry"] = retry
    if delay != 0.0: d["delay"] = delay
    if backoff != 1.0: d["backoff"] = backoff
    if jitter is not False: d["jitter"] = jitter
    if reraise is not True: d["reraise"] = reraise
    if log_level != 40: d["log_level"] = log_level
    if message is not None: d["log_format"] = message
    if retry_if is not None: d["retry_if"] = retry_if
    if retry_on_result is not None: d["retry_on_result"] = retry_on_result
    if on_error is not None: d["on_error"] = on_error
    if metrics is not False: d["metrics"] = metrics
    if metric_prefix != "": d["metric_prefix"] = metric_prefix
    if circuit_breaker is not None: d["circuit_breaker"] = circuit_breaker
    if stateful is not False: d["stateful"] = stateful
    if backoff_strategy is not None: d["backoff_strategy"] = backoff_strategy
    if max_delay is not None: d["max_delay"] = max_delay
    if reporters is not None: d["reporters"] = reporters
    if priority != 0: d["priority"] = priority
    if inject is not None: d["inject"] = inject
    return Policy(**d)

def handle(
    on: Union[Type[BaseException], tuple[Type[BaseException], ...]] = Exception,
    retry: int = 0,
    delay: float = 0.0,
    backoff: float = 1.0,
    jitter: bool = False,
    fallback: Optional[Callable[..., Any]] = None,
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
    backoff_strategy: str = "exponential",
    max_delay: Optional[float] = None,
    reporters: Optional[List] = None,
    priority: int = 0,
    inject: Optional[Dict[str, Any]] = None,
):
    merged = _merge_policy(policy, retry, delay, backoff, jitter, reraise, log_level, message,
                           retry_if, retry_on_result, on_error, metrics, metric_prefix,
                           circuit_breaker, stateful, backoff_strategy, max_delay,
                           reporters, priority, inject)
    catch_exceptions = on if isinstance(on, tuple) else (on,)
    state_counter = {}
    cb = merged.circuit_breaker
    is_async_cb = isinstance(cb, AsyncCircuitBreaker)

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for key, val in merged.inject.items():
                if key not in kwargs:
                    kwargs[key] = val

            logger = setup_logging(level=merged.log_level, fmt=merged.log_format)
            if cb and not is_async_cb:
                if not cb.allow_request():
                    if merged.reraise:
                        raise CircuitBreakerError("Circuit breaker is open")
                    if fallback:
                        return fallback(*args, **kwargs)
                    return None

            attempts = merged.retry + 1
            start_time = time.perf_counter()
            counter_key = f"{func.__module__}.{func.__name__}" if merged.stateful else None
            attempt_start = state_counter.get(counter_key, 0) if counter_key else 0

            for attempt in range(attempt_start, attempts):
                try:
                    result = func(*args, **kwargs)
                except catch_exceptions as e:
                    last_exc = e
                    if merged.on_error:
                        for exc_type, handler in merged.on_error.items():
                            if isinstance(e, exc_type):
                                handler(e)
                                break
                    can_retry = not merged.retry_if or merged.retry_if(e)
                    if can_retry and attempt < attempts - 1:
                        log_msg = merged.log_format.format(func=func.__name__, error=e, attempt=attempt+1) if merged.log_format else f"Error in {func.__name__}: {e} (attempt {attempt+1}/{attempts})"
                        logger.log(merged.log_level, log_msg)
                        for rep in merged.reporters:
                            rep.report(e, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})
                        if merged.metrics:
                            record_metric(merged.metric_prefix, func.__name__, 0, True)
                        if cb and not is_async_cb:
                            cb.record_failure()
                        t = compute_backoff(attempt, merged.delay, merged.backoff, merged.backoff_strategy, merged.max_delay)
                        time.sleep(apply_jitter(t, merged.jitter))
                        if counter_key:
                            state_counter[counter_key] = attempt + 1
                        continue
                    else:
                        if merged.reporters:
                            for rep in merged.reporters:
                                rep.report(e, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})
                        if cb and not is_async_cb:
                            cb.record_failure()
                        if fallback:
                            return fallback(*args, **kwargs)
                        if merged.reraise:
                            raise
                        return None
                else:
                    if merged.retry_on_result and merged.retry_on_result(result):
                        last_exc = ResultNotAcceptedError(f"Result not accepted: {result}")
                        if attempt < attempts - 1:
                            log_msg = merged.log_format.format(func=func.__name__, error=last_exc, attempt=attempt+1) if merged.log_format else f"Result not accepted in {func.__name__}: {result} (attempt {attempt+1}/{attempts})"
                            logger.log(merged.log_level, log_msg)
                            for rep in merged.reporters:
                                rep.report(last_exc, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})
                            t = compute_backoff(attempt, merged.delay, merged.backoff, merged.backoff_strategy, merged.max_delay)
                            time.sleep(apply_jitter(t, merged.jitter))
                            continue
                        else:
                            if merged.reraise:
                                raise last_exc
                            return result if not fallback else fallback(*args, **kwargs)
                    elapsed = time.perf_counter() - start_time
                    if merged.metrics:
                        record_metric(merged.metric_prefix, func.__name__, elapsed, False)
                    if cb and not is_async_cb:
                        cb.record_success()
                    if counter_key and counter_key in state_counter:
                        del state_counter[counter_key]
                    return result
            return None
        return wrapper
    return decorator

def handle_async(
    on: Union[Type[BaseException], tuple[Type[BaseException], ...]] = Exception,
    retry: int = 0,
    delay: float = 0.0,
    backoff: float = 1.0,
    jitter: bool = False,
    fallback: Optional[Callable[..., Any]] = None,
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
    backoff_strategy: str = "exponential",
    max_delay: Optional[float] = None,
    reporters: Optional[List] = None,
    priority: int = 0,
    inject: Optional[Dict[str, Any]] = None,
):
    merged = _merge_policy(policy, retry, delay, backoff, jitter, reraise, log_level, message,
                           retry_if, retry_on_result, on_error, metrics, metric_prefix,
                           circuit_breaker, stateful, backoff_strategy, max_delay,
                           reporters, priority, inject)
    catch_exceptions = on if isinstance(on, tuple) else (on,)
    state_counter = {}
    cb = merged.circuit_breaker
    is_async_cb = isinstance(cb, AsyncCircuitBreaker)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for key, val in merged.inject.items():
                if key not in kwargs:
                    kwargs[key] = val

            logger = setup_logging(level=merged.log_level, fmt=merged.log_format)
            if cb:
                if is_async_cb:
                    if not await cb.allow_request():
                        if merged.reraise:
                            raise CircuitBreakerError("Circuit breaker is open")
                        if fallback:
                            return fallback(*args, **kwargs)
                        return None
                else:
                    if not cb.allow_request():
                        if merged.reraise:
                            raise CircuitBreakerError("Circuit breaker is open")
                        if fallback:
                            return fallback(*args, **kwargs)
                        return None

            attempts = merged.retry + 1
            start_time = time.perf_counter()
            counter_key = f"{func.__module__}.{func.__name__}" if merged.stateful else None
            attempt_start = state_counter.get(counter_key, 0) if counter_key else 0

            for attempt in range(attempt_start, attempts):
                try:
                    result = await func(*args, **kwargs)
                except catch_exceptions as e:
                    last_exc = e
                    if merged.on_error:
                        for exc_type, handler in merged.on_error.items():
                            if isinstance(e, exc_type):
                                handler(e)
                                break
                    can_retry = not merged.retry_if or merged.retry_if(e)
                    if can_retry and attempt < attempts - 1:
                        log_msg = merged.log_format.format(func=func.__name__, error=e, attempt=attempt+1) if merged.log_format else f"Error in {func.__name__}: {e} (attempt {attempt+1}/{attempts})"
                        logger.log(merged.log_level, log_msg)
                        for rep in merged.reporters:
                            rep.report(e, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})
                        if merged.metrics:
                            record_metric(merged.metric_prefix, func.__name__, 0, True)
                        if cb:
                            if is_async_cb:
                                await cb.record_failure()
                            else:
                                cb.record_failure()
                        t = compute_backoff(attempt, merged.delay, merged.backoff, merged.backoff_strategy, merged.max_delay)
                        await asyncio.sleep(apply_jitter(t, merged.jitter))
                        if counter_key:
                            state_counter[counter_key] = attempt + 1
                        continue
                    else:
                        if merged.reporters:
                            for rep in merged.reporters:
                                rep.report(e, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})
                        if cb:
                            if is_async_cb:
                                await cb.record_failure()
                            else:
                                cb.record_failure()
                        if fallback:
                            return fallback(*args, **kwargs)
                        if merged.reraise:
                            raise
                        return None
                else:
                    if merged.retry_on_result and merged.retry_on_result(result):
                        last_exc = ResultNotAcceptedError(f"Result not accepted: {result}")
                        if attempt < attempts - 1:
                            log_msg = merged.log_format.format(func=func.__name__, error=last_exc, attempt=attempt+1) if merged.log_format else f"Result not accepted in {func.__name__}: {result} (attempt {attempt+1}/{attempts})"
                            logger.log(merged.log_level, log_msg)
                            for rep in merged.reporters:
                                rep.report(last_exc, {"func": func.__name__, "attempt": attempt+1, "args": args, "kwargs": kwargs})
                            t = compute_backoff(attempt, merged.delay, merged.backoff, merged.backoff_strategy, merged.max_delay)
                            await asyncio.sleep(apply_jitter(t, merged.jitter))
                            continue
                        else:
                            if merged.reraise:
                                raise last_exc
                            return result if not fallback else fallback(*args, **kwargs)
                    elapsed = time.perf_counter() - start_time
                    if merged.metrics:
                        record_metric(merged.metric_prefix, func.__name__, elapsed, False)
                    if cb:
                        if is_async_cb:
                            await cb.record_success()
                        else:
                            cb.record_success()
                    if counter_key and counter_key in state_counter:
                        del state_counter[counter_key]
                    return result
            return None
        return wrapper
    return decorator
