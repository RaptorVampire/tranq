import asyncio
import functools
import inspect
import logging
import time
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from .exceptions import CircuitBreakerError, ResultNotAcceptedError, FunctionTimeoutError
from .policies import Policy, get_global_policy
from .utils import (setup_logging, apply_jitter, compute_backoff,
                    _call_hook, _acall_hook, run_with_timeout)
from .circuit_breaker import CircuitBreaker
from .async_circuit_breaker import AsyncCircuitBreaker
from .metrics import record_metric

# None default avoids sharing a mutable dict across threads/tasks
_state_counter = ContextVar("state_counter", default=None)

# Python 3.9 compatible exception spec
ExcSpec = Union[Type[BaseException], Tuple[Type[BaseException], ...]]


def _get_state_dict():
    d = _state_counter.get()
    if d is None:
        d = {}
        _state_counter.set(d)
    return d


def _is_async_cb(cb) -> bool:
    if cb is None:
        return False
    return inspect.iscoroutinefunction(getattr(cb, "allow_request", None))


def _merge_policy(
    policy, retry, delay, backoff, jitter, reraise, log_level, message,
    retry_if=None, retry_on_result=None, on_error=None, metrics=False,
    metric_prefix="", circuit_breaker=None, stateful=False,
    backoff_strategy=None, max_delay=None, reporters=None, priority=0,
    inject=None, timeout=None, on_retry=None, on_success=None,
    on_failure=None, on_complete=None, retry_budget=None,
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
    if timeout is not None: d["timeout"] = timeout
    if on_retry is not None: d["on_retry"] = on_retry
    if on_success is not None: d["on_success"] = on_success
    if on_failure is not None: d["on_failure"] = on_failure
    if on_complete is not None: d["on_complete"] = on_complete
    if retry_budget is not None: d["retry_budget"] = retry_budget
    return Policy(**d)


def handle(
    on: ExcSpec = Exception,
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
    circuit_breaker=None,
    stateful: bool = False,
    backoff_strategy: str = "exponential",
    max_delay: Optional[float] = None,
    reporters: Optional[List] = None,
    priority: int = 0,
    inject: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
    on_retry: Optional[Callable] = None,
    on_success: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    retry_budget=None,
):
    if policy is None:
        policy = get_global_policy()

    eff_retry = retry if retry != 0 else policy.retry
    eff_delay = delay if delay != 0.0 else policy.delay
    eff_backoff = backoff if backoff != 1.0 else policy.backoff
    eff_jitter = jitter if jitter is not False else policy.jitter
    eff_reraise = reraise if reraise is not True else policy.reraise
    eff_log_level = log_level if log_level != 40 else policy.log_level
    eff_message = message if message is not None else policy.log_format
    eff_retry_if = retry_if if retry_if is not None else policy.retry_if
    eff_retry_on_result = retry_on_result if retry_on_result is not None else policy.retry_on_result
    eff_on_error = on_error if on_error is not None else policy.on_error
    eff_metrics = metrics if metrics is not False else policy.metrics
    eff_metric_prefix = metric_prefix if metric_prefix != "" else policy.metric_prefix
    eff_cb = circuit_breaker if circuit_breaker is not None else policy.circuit_breaker
    eff_stateful = stateful if stateful is not False else policy.stateful
    eff_backoff_strategy = backoff_strategy if backoff_strategy != "exponential" else policy.backoff_strategy
    eff_max_delay = max_delay if max_delay is not None else policy.max_delay
    eff_reporters = reporters if reporters is not None else policy.reporters
    eff_inject = inject if inject is not None else policy.inject
    eff_timeout = timeout if timeout is not None else policy.timeout
    eff_on_retry = on_retry if on_retry is not None else policy.on_retry
    eff_on_success = on_success if on_success is not None else policy.on_success
    eff_on_failure = on_failure if on_failure is not None else policy.on_failure
    eff_on_complete = on_complete if on_complete is not None else policy.on_complete
    eff_retry_budget = retry_budget if retry_budget is not None else policy.retry_budget

    catch_exceptions = on if isinstance(on, tuple) else (on,)
    cb = eff_cb
    is_async_cb = _is_async_cb(cb)

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for key, val in eff_inject.items():
                if key not in kwargs:
                    kwargs[key] = val

            logger = setup_logging(level=eff_log_level, fmt=eff_message)

            if eff_retry_budget is not None:
                eff_retry_budget.record_call()

            if cb and not is_async_cb:
                if not cb.allow_request():
                    if eff_reraise:
                        raise CircuitBreakerError("Circuit breaker is open")
                    if fallback:
                        return fallback(*args, **kwargs)
                    return None

            attempts = eff_retry + 1
            start_time = time.perf_counter()
            counter_key = f"{func.__module__}.{func.__name__}" if eff_stateful else None
            state_dict = _get_state_dict() if counter_key else {}
            attempt_start = state_dict.get(counter_key, 0) if counter_key else 0

            for attempt in range(attempt_start, attempts):
                try:
                    if eff_timeout is not None:
                        result = run_with_timeout(func, args, kwargs, eff_timeout)
                    else:
                        result = func(*args, **kwargs)
                except catch_exceptions as e:
                    if eff_metrics:
                        record_metric(eff_metric_prefix, func.__name__, 0, True)

                    handled = False
                    if eff_on_error:
                        for exc_type, handler in eff_on_error.items():
                            if isinstance(e, exc_type):
                                handler(e)
                                handled = True
                                break

                    if handled:
                        if cb and not is_async_cb:
                            cb.record_failure()
                        _call_hook(eff_on_failure, e)
                        _call_hook(eff_on_complete)
                        if fallback is not None:
                            return fallback(*args, **kwargs)
                        if eff_reraise:
                            raise
                        return None

                    should_retry = True
                    if eff_retry_if is not None:
                        should_retry = eff_retry_if(e)
                    if eff_retry_budget is not None and not eff_retry_budget.allow_retry():
                        should_retry = False

                    if should_retry and attempt < attempts - 1:
                        _call_hook(eff_on_retry, e, attempt + 1)
                        log_msg = eff_message.format(
                            func=func.__name__, error=e, attempt=attempt + 1
                        ) if eff_message else f"Error in {func.__name__}: {e} (attempt {attempt + 1}/{attempts})"
                        logger.log(eff_log_level, log_msg)
                        for rep in eff_reporters:
                            rep.report(e, {"func": func.__name__, "attempt": attempt + 1,
                                           "args": args, "kwargs": kwargs})
                        if cb and not is_async_cb:
                            cb.record_failure()
                        t = compute_backoff(attempt, eff_delay, eff_backoff,
                                            eff_backoff_strategy, eff_max_delay)
                        time.sleep(apply_jitter(t, eff_jitter))
                        if counter_key:
                            state_dict[counter_key] = attempt + 1
                            _state_counter.set(state_dict)
                        continue
                    else:
                        for rep in eff_reporters:
                            rep.report(e, {"func": func.__name__, "attempt": attempt + 1,
                                           "args": args, "kwargs": kwargs})
                        if cb and not is_async_cb:
                            cb.record_failure()
                        _call_hook(eff_on_failure, e)
                        _call_hook(eff_on_complete)
                        if fallback is not None:
                            return fallback(*args, **kwargs)
                        if eff_reraise:
                            raise
                        return None
                else:
                    if eff_retry_on_result and eff_retry_on_result(result):
                        if attempt < attempts - 1:
                            logger.log(eff_log_level,
                                       f"Result not accepted in {func.__name__} (attempt {attempt + 1}/{attempts})")
                            for rep in eff_reporters:
                                rep.report(ResultNotAcceptedError(str(result)),
                                           {"func": func.__name__, "attempt": attempt + 1})
                            t = compute_backoff(attempt, eff_delay, eff_backoff,
                                                eff_backoff_strategy, eff_max_delay)
                            time.sleep(apply_jitter(t, eff_jitter))
                            continue
                        else:
                            _call_hook(eff_on_failure, ResultNotAcceptedError(str(result)))
                            _call_hook(eff_on_complete)
                            if eff_reraise:
                                raise ResultNotAcceptedError(f"Result not accepted: {result}")
                            return result if fallback is None else fallback(*args, **kwargs)

                    # success path
                    elapsed = time.perf_counter() - start_time
                    if eff_metrics:
                        record_metric(eff_metric_prefix, func.__name__, elapsed, False)
                    if cb and not is_async_cb:
                        cb.record_success()
                    if counter_key and counter_key in state_dict:
                        del state_dict[counter_key]
                        _state_counter.set(state_dict)
                    _call_hook(eff_on_success, result)
                    _call_hook(eff_on_complete)
                    return result

            return None

        return wrapper

    return decorator


def handle_async(
    on: ExcSpec = Exception,
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
    circuit_breaker=None,
    stateful: bool = False,
    backoff_strategy: str = "exponential",
    max_delay: Optional[float] = None,
    reporters: Optional[List] = None,
    priority: int = 0,
    inject: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
    on_retry: Optional[Callable] = None,
    on_success: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    retry_budget=None,
):
    if policy is None:
        policy = get_global_policy()

    eff_retry = retry if retry != 0 else policy.retry
    eff_delay = delay if delay != 0.0 else policy.delay
    eff_backoff = backoff if backoff != 1.0 else policy.backoff
    eff_jitter = jitter if jitter is not False else policy.jitter
    eff_reraise = reraise if reraise is not True else policy.reraise
    eff_log_level = log_level if log_level != 40 else policy.log_level
    eff_message = message if message is not None else policy.log_format
    eff_retry_if = retry_if if retry_if is not None else policy.retry_if
    eff_retry_on_result = retry_on_result if retry_on_result is not None else policy.retry_on_result
    eff_on_error = on_error if on_error is not None else policy.on_error
    eff_metrics = metrics if metrics is not False else policy.metrics
    eff_metric_prefix = metric_prefix if metric_prefix != "" else policy.metric_prefix
    eff_cb = circuit_breaker if circuit_breaker is not None else policy.circuit_breaker
    eff_stateful = stateful if stateful is not False else policy.stateful
    eff_backoff_strategy = backoff_strategy if backoff_strategy != "exponential" else policy.backoff_strategy
    eff_max_delay = max_delay if max_delay is not None else policy.max_delay
    eff_reporters = reporters if reporters is not None else policy.reporters
    eff_inject = inject if inject is not None else policy.inject
    eff_timeout = timeout if timeout is not None else policy.timeout
    eff_on_retry = on_retry if on_retry is not None else policy.on_retry
    eff_on_success = on_success if on_success is not None else policy.on_success
    eff_on_failure = on_failure if on_failure is not None else policy.on_failure
    eff_on_complete = on_complete if on_complete is not None else policy.on_complete
    eff_retry_budget = retry_budget if retry_budget is not None else policy.retry_budget

    catch_exceptions = on if isinstance(on, tuple) else (on,)
    cb = eff_cb
    is_async_cb = _is_async_cb(cb)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for key, val in eff_inject.items():
                if key not in kwargs:
                    kwargs[key] = val

            logger = setup_logging(level=eff_log_level, fmt=eff_message)

            if eff_retry_budget is not None:
                eff_retry_budget.record_call()

            if cb:
                allowed = await cb.allow_request() if is_async_cb else cb.allow_request()
                if not allowed:
                    if eff_reraise:
                        raise CircuitBreakerError("Circuit breaker is open")
                    if fallback:
                        return fallback(*args, **kwargs)
                    return None

            attempts = eff_retry + 1
            start_time = time.perf_counter()
            counter_key = f"{func.__module__}.{func.__name__}" if eff_stateful else None
            state_dict = _get_state_dict() if counter_key else {}
            attempt_start = state_dict.get(counter_key, 0) if counter_key else 0

            for attempt in range(attempt_start, attempts):
                try:
                    if eff_timeout is not None:
                        try:
                            result = await asyncio.wait_for(func(*args, **kwargs), eff_timeout)
                        except asyncio.TimeoutError:
                            raise FunctionTimeoutError(
                                f"{func.__name__} timed out after {eff_timeout}s")
                    else:
                        result = await func(*args, **kwargs)
                except catch_exceptions as e:
                    if eff_metrics:
                        record_metric(eff_metric_prefix, func.__name__, 0, True)

                    handled = False
                    if eff_on_error:
                        for exc_type, handler in eff_on_error.items():
                            if isinstance(e, exc_type):
                                handler(e)
                                handled = True
                                break

                    if handled:
                        if cb:
                            if is_async_cb:
                                await cb.record_failure()
                            else:
                                cb.record_failure()
                        await _acall_hook(eff_on_failure, e)
                        await _acall_hook(eff_on_complete)
                        if fallback is not None:
                            return fallback(*args, **kwargs)
                        if eff_reraise:
                            raise
                        return None

                    should_retry = True
                    if eff_retry_if is not None:
                        should_retry = eff_retry_if(e)
                    if eff_retry_budget is not None and not eff_retry_budget.allow_retry():
                        should_retry = False

                    if should_retry and attempt < attempts - 1:
                        await _acall_hook(eff_on_retry, e, attempt + 1)
                        log_msg = eff_message.format(
                            func=func.__name__, error=e, attempt=attempt + 1
                        ) if eff_message else f"Error in {func.__name__}: {e} (attempt {attempt + 1}/{attempts})"
                        logger.log(eff_log_level, log_msg)
                        for rep in eff_reporters:
                            rep.report(e, {"func": func.__name__, "attempt": attempt + 1,
                                           "args": args, "kwargs": kwargs})
                        if cb:
                            if is_async_cb:
                                await cb.record_failure()
                            else:
                                cb.record_failure()
                        t = compute_backoff(attempt, eff_delay, eff_backoff,
                                            eff_backoff_strategy, eff_max_delay)
                        await asyncio.sleep(apply_jitter(t, eff_jitter))
                        if counter_key:
                            state_dict[counter_key] = attempt + 1
                            _state_counter.set(state_dict)
                        continue
                    else:
                        for rep in eff_reporters:
                            rep.report(e, {"func": func.__name__, "attempt": attempt + 1,
                                           "args": args, "kwargs": kwargs})
                        if cb:
                            if is_async_cb:
                                await cb.record_failure()
                            else:
                                cb.record_failure()
                        await _acall_hook(eff_on_failure, e)
                        await _acall_hook(eff_on_complete)
                        if fallback is not None:
                            return fallback(*args, **kwargs)
                        if eff_reraise:
                            raise
                        return None
                else:
                    if eff_retry_on_result and eff_retry_on_result(result):
                        if attempt < attempts - 1:
                            logger.log(eff_log_level,
                                       f"Result not accepted in {func.__name__} (attempt {attempt + 1}/{attempts})")
                            for rep in eff_reporters:
                                rep.report(ResultNotAcceptedError(str(result)),
                                           {"func": func.__name__, "attempt": attempt + 1})
                            t = compute_backoff(attempt, eff_delay, eff_backoff,
                                                eff_backoff_strategy, eff_max_delay)
                            await asyncio.sleep(apply_jitter(t, eff_jitter))
                            continue
                        else:
                            await _acall_hook(eff_on_failure, ResultNotAcceptedError(str(result)))
                            await _acall_hook(eff_on_complete)
                            if eff_reraise:
                                raise ResultNotAcceptedError(f"Result not accepted: {result}")
                            return result if fallback is None else fallback(*args, **kwargs)

                    # success path
                    elapsed = time.perf_counter() - start_time
                    if eff_metrics:
                        record_metric(eff_metric_prefix, func.__name__, elapsed, False)
                    if cb:
                        if is_async_cb:
                            await cb.record_success()
                        else:
                            cb.record_success()
                    if counter_key and counter_key in state_dict:
                        del state_dict[counter_key]
                        _state_counter.set(state_dict)
                    await _acall_hook(eff_on_success, result)
                    await _acall_hook(eff_on_complete)
                    return result

            return None

        return wrapper

    return decorator
