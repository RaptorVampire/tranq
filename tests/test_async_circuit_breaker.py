import asyncio
import pytest
from tranq import AsyncCircuitBreaker

@pytest.mark.asyncio
class TestAsyncCircuitBreaker:
    async def test_closed_to_open(self):
        cb = AsyncCircuitBreaker(failure_threshold=2, timeout=0.1)
        assert await cb.state == "closed"
        await cb.record_failure()
        assert await cb.state == "closed"
        await cb.record_failure()
        assert await cb.state == "open"

    async def test_open_to_half_open(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=0.1)
        await cb.record_failure()
        await asyncio.sleep(0.15)
        assert await cb.allow_request()
        assert await cb.state == "half-open"

    async def test_half_open_to_closed(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=0.1)
        await cb.record_failure()
        await asyncio.sleep(0.15)
        await cb.allow_request()
        await cb.record_success()
        assert await cb.state == "closed"

    async def test_half_open_to_open(self):
        cb = AsyncCircuitBreaker(failure_threshold=2, timeout=0.1)
        await cb.record_failure()
        await cb.record_failure()
        await asyncio.sleep(0.15)
        await cb.allow_request()
        await cb.record_failure()
        assert await cb.state == "open"

    async def test_half_open_limits(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=0.1, half_open_requests=2)
        await cb.record_failure()
        await asyncio.sleep(0.15)
        assert await cb.allow_request()
        assert await cb.allow_request()
        assert not await cb.allow_request()
