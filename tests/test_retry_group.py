import pytest
import asyncio
from tranq import retry_group, async_retry_group, CircuitBreaker, CircuitBreakerError, AsyncCircuitBreaker
class TestSyncRetryGroup:
    def test_all_success(self):
        assert retry_group(lambda: 1, lambda: 2, on=Exception, retry=0).run() == [1, 2]

    def test_retry_success(self):
        calls = 0
        def flaky():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert retry_group(lambda: 1, flaky, on=ValueError, retry=2).run() == [1, "ok"]

    def test_exhausted(self):
        assert retry_group(lambda: 1/0, on=ZeroDivisionError, retry=1, reraise=False).run() is None

    def test_retry_if(self):
        g = retry_group(lambda: exec('raise ValueError("normal")'), on=ValueError, retry=1,
                        retry_if=lambda e: "retry" in str(e))
        with pytest.raises(ValueError): g.run()

    def test_on_error(self):
        called = []
        g = retry_group(lambda: exec('raise ValueError("oops")'), on=ValueError, retry=0, reraise=False,
                        on_error={ValueError: lambda e: called.append(1)})
        g.run()
        assert len(called) == 1

    def test_fallback(self):
        g = retry_group(lambda: exec('raise ValueError("fail")'), on=ValueError, retry=0,
                        fallback=lambda: ["fb"])
        assert g.run() == ["fb"]

    def test_stateful(self):
        counter = 0
        def flaky():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        g = retry_group(flaky, on=ValueError, retry=2, stateful=True, reraise=False)
        assert g.run() == ["ok"]
        assert counter == 3

    def test_reporters(self):
        reports = []
        class R:
            def report(self, e, ctx): reports.append(e)
        g = retry_group(lambda: exec('raise ValueError("boom")'), on=ValueError, retry=0, reraise=False,
                        reporters=[R()])
        g.run()
        assert len(reports) == 1

    def test_circuit_breaker(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=10)
        g = retry_group(lambda: exec('raise ValueError("fail")'), on=ValueError, retry=0, circuit_breaker=cb)
        with pytest.raises(ValueError): g.run()
        with pytest.raises(CircuitBreakerError): g.run()

@pytest.mark.asyncio
class TestAsyncRetryGroup:
    async def test_all_success(self):
        async def a(): return 1
        assert await async_retry_group(a, lambda: 2, on=Exception, retry=0).run() == [1, 2]

    async def test_retry_success(self):
        calls = 0
        async def flaky():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert await async_retry_group(lambda: 1, flaky, on=ValueError, retry=2).run() == [1, "ok"]

    async def test_on_error(self):
        called = []
        async def f(): raise ValueError("oops")
        g = async_retry_group(f, on=ValueError, retry=0, reraise=False,
                              on_error={ValueError: lambda e: called.append(1)})
        await g.run()
        assert len(called) == 1

    async def test_fallback(self):
        async def f(): raise ValueError("fail")
        g = async_retry_group(f, on=ValueError, retry=0, fallback=lambda: ["fb"])
        assert await g.run() == ["fb"]

    async def test_stateful(self):
        counter = 0
        async def flaky():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        g = async_retry_group(flaky, on=ValueError, retry=2, stateful=True, reraise=False)
        assert await g.run() == ["ok"]
        assert counter == 3

    async def test_circuit_breaker(self):
        cb = AsyncCircuitBreaker(failure_threshold=1, timeout=10)
        async def f(): raise ValueError("fail")
        g = async_retry_group(f, on=ValueError, retry=0, circuit_breaker=cb)
        with pytest.raises(ValueError): await g.run()
        with pytest.raises(CircuitBreakerError): await g.run()
