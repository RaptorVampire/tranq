import asyncio
import logging
from unittest.mock import patch, MagicMock
import pytest
from tranq import (
    handle_async, CircuitBreaker, AsyncCircuitBreaker, CircuitBreakerError
)

@pytest.mark.asyncio
class TestHandleAsync:
    async def test_basic_retry(self):
        calls = 0
        @handle_async(on=ValueError, retry=2)
        async def f():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert await f() == "ok"

    async def test_retry_if_async(self):
        @handle_async(on=Exception, retry=1, retry_if=lambda e: "429" in str(e))
        async def f(code):
            raise Exception(f"status {code}")
        with pytest.raises(Exception): await f(500)
        with pytest.raises(Exception): await f(429)

    async def test_sync_circuit_breaker_in_async(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=10)
        @handle_async(on=ValueError, circuit_breaker=cb, retry=0)
        async def f(): raise ValueError("fail")
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()

    async def test_async_circuit_breaker(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=10)
        @handle_async(on=ValueError, circuit_breaker=cb, retry=0)
        async def f(): raise ValueError("fail")
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()

    async def test_async_circuit_breaker_half_open(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=0.1)
        @handle_async(on=ValueError, circuit_breaker=cb, retry=0)
        async def f(): raise ValueError("fail")
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()
        await asyncio.sleep(0.15)
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()

    async def test_retry_on_result_async(self):
        results = [0, 1]
        @handle_async(retry=1, retry_on_result=lambda r: r == 0, reraise=False)
        async def f(): return results.pop(0)
        assert await f() == 1

    async def test_on_error_async(self):
        handler = MagicMock()
        @handle_async(on=ValueError, on_error={ValueError: handler}, reraise=False)
        async def f(): raise ValueError("oops")
        await f()
        handler.assert_called_once()

    async def test_stateful_async(self):
        counter = 0
        @handle_async(on=ValueError, retry=2, stateful=True, reraise=False)
        async def f():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        assert await f() == "ok"
        assert counter == 3
