import asyncio
import logging
from unittest.mock import MagicMock
import pytest
from tranq import (
    handle_async, CircuitBreaker, AsyncCircuitBreaker, CircuitBreakerError,
    ResultNotAcceptedError, set_global_policy, Policy, get_metrics, reset_metrics
)

@pytest.fixture(autouse=True)
def reset_state():
    reset_metrics()
    set_global_policy(Policy())
    yield

@pytest.mark.asyncio
class TestAsyncBasic:
    async def test_retry_success(self):
        calls = 0
        @handle_async(on=ValueError, retry=2)
        async def f():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert await f() == "ok"
        assert calls == 3

    async def test_fallback(self):
        @handle_async(on=ValueError, retry=0, fallback=lambda: "safe", reraise=False)
        async def f(): raise ValueError("fail")
        assert await f() == "safe"

@pytest.mark.asyncio
class TestAsyncRetryIf:
    async def test_retry_if(self):
        @handle_async(on=Exception, retry=1, retry_if=lambda e: "429" in str(e))
        async def f(code): raise Exception(f"status {code}")
        with pytest.raises(Exception): await f(500)
        with pytest.raises(Exception): await f(429)

@pytest.mark.asyncio
class TestAsyncRetryOnResult:
    async def test_retry_on_result(self):
        results = [0, 1]
        @handle_async(retry=1, retry_on_result=lambda r: r == 0, reraise=False)
        async def f(): return results.pop(0)
        assert await f() == 1

@pytest.mark.asyncio
class TestAsyncOnError:
    async def test_on_error(self):
        called = []
        @handle_async(on=ValueError, on_error={ValueError: lambda e: called.append(1)}, reraise=False)
        async def f(): raise ValueError("oops")
        await f()
        assert len(called) == 1

@pytest.mark.asyncio
class TestAsyncCircuitBreaker:
    async def test_sync_cb_in_async(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=10)
        @handle_async(on=ValueError, circuit_breaker=cb, retry=0)
        async def f(): raise ValueError("fail")
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()

    async def test_async_cb(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=10)
        @handle_async(on=ValueError, circuit_breaker=cb, retry=0)
        async def f(): raise ValueError("fail")
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()

    async def test_async_cb_half_open(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=0.1)
        @handle_async(on=ValueError, circuit_breaker=cb, retry=0)
        async def f(): raise ValueError("fail")
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()
        await asyncio.sleep(0.15)
        with pytest.raises(ValueError): await f()
        with pytest.raises(CircuitBreakerError): await f()

@pytest.mark.asyncio
class TestAsyncStateful:
    async def test_stateful(self):
        counter = 0
        @handle_async(on=ValueError, retry=2, stateful=True, reraise=False)
        async def f():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        assert await f() == "ok"
        assert counter == 3

@pytest.mark.asyncio
class TestAsyncInject:
    async def test_inject(self):
        @handle_async(inject={"service": "db"})
        async def f(service=None): return service
        assert await f() == "db"
