import pytest
from tranq import wait, stop


class TestWaitStrategies:
    def test_fixed(self):
        w = wait.fixed(1.0)
        assert w(0) == 1.0 and w(5) == 1.0

    def test_none(self):
        assert wait.none()(3) == 0.0

    def test_exponential(self):
        w = wait.exponential(multiplier=1.0, exp_base=2.0)
        assert w(0) == 1.0
        assert w(1) == 2.0
        assert w(2) == 4.0

    def test_exponential_max(self):
        w = wait.exponential(multiplier=1.0, max=3.0)
        assert w(10) == 3.0

    def test_exponential_min(self):
        w = wait.exponential(multiplier=0.1, min=1.0)
        assert w(0) == 1.0

    def test_linear(self):
        w = wait.incrementing(start=0.0, increment=0.5)
        assert w(0) == 0.0
        assert w(2) == 1.0

    def test_fibonacci(self):
        w = wait.fibonacci(multiplier=1.0)
        vals = [w(i) for i in range(5)]
        # Fibonacci sequence: 1, 1, 2, 3, 5 (matches utils.compute_backoff)
        assert vals[0] == 1.0 and vals[1] == 1.0 and vals[4] == 5.0

    def test_full_jitter_in_range(self):
        w = wait.full_jitter(multiplier=1.0, max=10.0)
        for a in range(5):
            assert 0 <= w(a) <= 10.0

    def test_equal_jitter(self):
        w = wait.equal_jitter(multiplier=2.0)
        for a in range(5):
            v = w(a)
            assert v >= 0

    def test_decorrelate_in_range(self):
        w = wait.decorrelate_jitter(base=1.0, cap=10.0)
        for a in range(10):
            assert 0 <= w(a) <= 10.0

    def test_combine(self):
        w = wait.fixed(1.0) + wait.fixed(2.0)
        assert w(0) == 3.0


class TestStopConditions:
    def test_after_attempt(self):
        s = stop.after_attempt(3)
        assert not s(2, 0)
        assert s(3, 0)

    def test_after_delay(self):
        s = stop.after_delay(5.0)
        assert not s(1, 4.9)
        assert s(1, 5.1)

    def test_never(self):
        assert not stop.never()(100, 1000)

    def test_and(self):
        s = stop.after_attempt(3) & stop.after_delay(5.0)
        assert not s(3, 1.0)   # attempt met, delay not
        assert s(3, 6.0)       # both met

    def test_or(self):
        s = stop.after_attempt(3) | stop.after_delay(5.0)
        assert s(3, 1.0)       # attempt met
        assert s(1, 6.0)       # delay met
        assert not s(1, 1.0)   # neither
