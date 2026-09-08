import time
import pytest
from tranq import SlidingWindowCircuitBreaker, AsyncSlidingWindowCircuitBreaker


class TestSlidingWindowSync:
    def test_opens_on_failure_rate(self):
        cb = SlidingWindowCircuitBreaker(
            window_size=10, failure_rate_threshold=0.5, timeout=0.1, minimum_calls=3)
        assert cb.state == "closed"
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "open"

    def test_stays_closed_below_threshold(self):
        cb = SlidingWindowCircuitBreaker(
            window_size=10, failure_rate_threshold=0.5, minimum_calls=4)
        cb.record_success()
        cb.record_success()
        cb.record_success()
        cb.record_failure()
        assert cb.state == "closed"

    def test_half_open_and_close(self):
        cb = SlidingWindowCircuitBreaker(
            window_size=10, failure_rate_threshold=0.5, timeout=0.05, minimum_calls=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        assert not cb.allow_request()
        time.sleep(0.1)
        assert cb.allow_request()
        cb.record_success()
        assert cb.state == "closed"

    def test_failure_rate(self):
        cb = SlidingWindowCircuitBreaker(window_size=10, minimum_calls=100)
        cb.record_success()
        cb.record_failure()
        assert abs(cb.failure_rate - 0.5) < 0.01

    def test_reset(self):
        cb = SlidingWindowCircuitBreaker(
            window_size=10, failure_rate_threshold=0.5, minimum_calls=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        cb.reset()
        assert cb.state == "closed"


@pytest.mark.asyncio
class TestSlidingWindowAsync:
    async def test_opens(self):
        cb = AsyncSlidingWindowCircuitBreaker(
            window_size=10, failure_rate_threshold=0.5, minimum_calls=2)
        await cb.record_failure()
        await cb.record_failure()
        assert await cb.state == "open"
