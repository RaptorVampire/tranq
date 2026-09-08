import time
import asyncio
import pytest
from tranq import RateLimiter, rate_limit, RateLimitExceeded


class TestRateLimiterCore:
    def test_initial_capacity(self):
        rl = RateLimiter(rate=5, per=1.0, burst=5)
        for _ in range(5):
            assert rl.try_acquire()
        assert not rl.try_acquire()

    def test_refill(self):
        rl = RateLimiter(rate=100, per=1.0, burst=1)
        assert rl.try_acquire()
        assert not rl.try_acquire()
        time.sleep(0.05)
        assert rl.try_acquire()

    def test_acquire_timeout_zero(self):
        rl = RateLimiter(rate=1, per=10.0, burst=1)
        assert rl.acquire(timeout=0)
        assert not rl.acquire(timeout=0)


class TestRateLimitDecorator:
    def test_decorator_attaches_limiter(self):
        @rate_limit(rate=10, per=1.0)
        def f():
            return 1
        assert hasattr(f, "rate_limiter")
        assert f() == 1

    def test_raises_when_exhausted(self):
        @rate_limit(rate=1, per=10.0, burst=1, timeout=0, raise_on_limit=True)
        def f():
            return 1
        assert f() == 1
        with pytest.raises(RateLimitExceeded):
            f()

    def test_no_raise_returns_none(self):
        @rate_limit(rate=1, per=10.0, burst=1, timeout=0, raise_on_limit=False)
        def f():
            return 1
        assert f() == 1
        assert f() is None

    def test_async_decorator(self):
        @rate_limit(rate=1, per=10.0, burst=1, timeout=0)
        async def f():
            return "ok"

        async def run():
            first = await f()
            try:
                await f()
                return first, None
            except RateLimitExceeded:
                return first, "raised"

        first, status = asyncio.run(run())
        assert first == "ok"
        assert status == "raised"
