"""Wait (backoff) strategies. All strategies are callables: wait(attempt) -> seconds.

Strategies:
    wait_none, wait_fixed, wait_random, wait_incrementing (linear),
    wait_exponential, wait_fibonacci, wait_random_exponential (full jitter),
    wait_equal_jitter, wait_decorrelate_jitter, wait_combine.

Every strategy supports ``min`` / ``max`` clamping and is composable with ``+``.
"""
import random


class wait_base:
    """Base class for all wait strategies."""

    def __call__(self, attempt: int) -> float:
        raise NotImplementedError

    def __add__(self, other):
        return wait_combine(self, other)

    @staticmethod
    def _clamp(value, mn, mx):
        if mn is not None and value < mn:
            value = mn
        if mx is not None and value > mx:
            value = mx
        return value


class wait_none(wait_base):
    """No waiting at all."""

    def __call__(self, attempt):
        return 0.0


class wait_fixed(wait_base):
    """Constant / fixed delay between retries."""

    def __init__(self, wait: float = 1.0):
        self.wait = wait

    def __call__(self, attempt):
        return self.wait


class wait_random(wait_base):
    """Random delay uniformly distributed between min and max."""

    def __init__(self, min: float = 0.0, max: float = 1.0):
        self.min = min
        self.max = max

    def __call__(self, attempt):
        return random.uniform(self.min, self.max)


class wait_incrementing(wait_base):
    """Linear backoff: start + increment * attempt."""

    def __init__(self, start: float = 0.0, increment: float = 1.0,
                 min: float = None, max: float = None):
        self.start = start
        self.increment = increment
        self.min = min
        self.max = max

    def __call__(self, attempt):
        v = self.start + self.increment * attempt
        return self._clamp(v, self.min, self.max)


class wait_exponential(wait_base):
    """Exponential backoff: multiplier * (exp_base ** attempt)."""

    def __init__(self, multiplier: float = 1.0, min: float = None,
                 max: float = None, exp_base: float = 2.0):
        self.multiplier = multiplier
        self.min = min
        self.max = max
        self.exp_base = exp_base

    def __call__(self, attempt):
        v = self.multiplier * (self.exp_base ** attempt)
        return self._clamp(v, self.min, self.max)


class wait_fibonacci(wait_base):
    """Fibonacci backoff: multiplier * fib(attempt)."""

    def __init__(self, multiplier: float = 1.0, min: float = None, max: float = None):
        self.multiplier = multiplier
        self.min = min
        self.max = max

    def __call__(self, attempt):
        a, b = 1, 1
        for _ in range(attempt):
            a, b = b, a + b
        v = self.multiplier * a
        return self._clamp(v, self.min, self.max)


class wait_random_exponential(wait_base):
    """Full jitter: uniform random in [0, exponential(attempt)]."""

    def __init__(self, multiplier: float = 1.0, min: float = 0.0,
                 max: float = None, exp_base: float = 2.0):
        self.exp = wait_exponential(multiplier=multiplier, max=max, exp_base=exp_base)
        self.min = min

    def __call__(self, attempt):
        high = self.exp(attempt)
        return random.uniform(self.min, high)


class wait_equal_jitter(wait_base):
    """Equal jitter: half fixed + half random of the exponential value."""

    def __init__(self, multiplier: float = 1.0, min: float = None,
                 max: float = None, exp_base: float = 2.0):
        self.exp = wait_exponential(multiplier=multiplier, max=max, exp_base=exp_base)
        self.min = min

    def __call__(self, attempt):
        v = self.exp(attempt)
        out = v / 2.0 + random.uniform(0, v / 2.0)
        if self.min is not None and out < self.min:
            out = self.min
        return out


class wait_decorrelate_jitter(wait_base):
    """Decorrelated jitter (AWS style): sleep = min(cap, rand(base, prev*3)).

    Stateful per instance. Use one instance per call site.
    """

    def __init__(self, base: float = 1.0, cap: float = None):
        self.base = base
        self.cap = cap
        self._last = base

    def __call__(self, attempt):
        high = self._last * 3.0
        v = random.uniform(self.base, high)
        if self.cap is not None and v > self.cap:
            v = self.cap
        self._last = v
        return v

    def reset(self):
        self._last = self.base


class wait_combine(wait_base):
    """Sum of multiple wait strategies."""

    def __init__(self, *strategies):
        self.strategies = strategies

    def __call__(self, attempt):
        return sum(s(attempt) for s in self.strategies)


# Friendly namespace ------------------------------------------------------
class wait:
    """Namespace with factory helpers."""
    none = wait_none
    fixed = wait_fixed
    random = wait_random
    incrementing = wait_incrementing
    linear = wait_incrementing
    exponential = wait_exponential
    fibonacci = wait_fibonacci
    random_exponential = wait_random_exponential
    full_jitter = wait_random_exponential
    equal_jitter = wait_equal_jitter
    decorrelate_jitter = wait_decorrelate_jitter
    combine = wait_combine

    @staticmethod
    def exponential_jitter(initial: float = 1.0, max: float = 60.0,
                           exp_base: float = 2.0, jitter: float = 1.0):
        """Exponential with additive jitter (Google style)."""
        exp = wait_exponential(multiplier=initial, max=max, exp_base=exp_base)

        def _w(attempt):
            return exp(attempt) + random.uniform(0, jitter)
        return _w
