"""Chaos / resilience testing: inject latency, errors and timeouts."""
import time
import random
from contextlib import contextmanager

_chaos_reports = []


class ChaosConfig:
    def __init__(self, latency: float = 0.0, error_rate: float = 0.0,
                 timeout_rate: float = 0.0, error_type=RuntimeError, seed=None):
        self.latency = latency
        self.error_rate = error_rate
        self.timeout_rate = timeout_rate
        self.error_type = error_type
        self.rng = random.Random(seed) if seed is not None else random


@contextmanager
def chaos(latency: float = 0.0, error_rate: float = 0.0,
          timeout_rate: float = 0.0, error_type=RuntimeError, seed=None):
    """Context manager exposing a chaos injector.

    Inside the block, call ``injector.maybe_inject()`` at operation boundaries
    to apply the configured chaos, or decorate with ``@chaos_wrapped``.
    """
    cfg = ChaosConfig(latency, error_rate, timeout_rate, error_type, seed)
    injector = ChaosInjector(cfg)
    try:
        yield injector
    finally:
        _chaos_reports.append(injector.report())


class ChaosInjector:
    def __init__(self, config: ChaosConfig):
        self.config = config
        self.counters = {"latency": 0, "errors": 0, "timeouts": 0, "clean": 0}

    def maybe_inject(self):
        cfg = self.config
        injected = False
        if cfg.latency > 0:
            time.sleep(cfg.latency)
            self.counters["latency"] += 1
            injected = True
        if cfg.timeout_rate > 0 and cfg.rng.random() < cfg.timeout_rate:
            self.counters["timeouts"] += 1
            raise TimeoutError("chaos: injected timeout")
        if cfg.error_rate > 0 and cfg.rng.random() < cfg.error_rate:
            self.counters["errors"] += 1
            raise cfg.error_type("chaos: injected error")
        if not injected:
            self.counters["clean"] += 1

    def report(self):
        return dict(self.counters)


def chaos_wrapped(injector: ChaosInjector):
    """Decorator applying chaos injection before each call."""
    def decorator(func):
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            injector.maybe_inject()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def chaos_report() -> list:
    """Return reports from all chaos sessions started in this process."""
    return list(_chaos_reports)


def reset_chaos_reports():
    _chaos_reports.clear()
