import pytest
import asyncio
from tranq import AsyncCircuitBreaker

@pytest.mark.asyncio
async def test_async_circuit_breaker_transitions():
    cb = AsyncCircuitBreaker(failure_threshold=2, timeout=0.1)
    assert cb.state == "closed"
    await cb.record_failure()
    assert cb.state == "closed"
    await cb.record_failure()
    assert cb.state == "open"
    await asyncio.sleep(0.15)
    assert await cb.allow_request()
    assert cb.state == "half-open"
    await cb.record_success()
    assert cb.state == "closed"
