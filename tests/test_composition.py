import pytest
from tranq import PolicyBuilder, resilient, wait, stop, retry_if, EventBus


class TestPolicyBuilder:
    def test_basic_retry(self):
        calls = [0]

        @PolicyBuilder().retry(max_attempts=3, wait=wait.fixed(0))
        def f():
            calls[0] += 1
            if calls[0] < 3:
                raise ValueError("fail")
            return "ok"

        assert f() == "ok"
        assert calls[0] == 3

    def test_stop_condition(self):
        calls = [0]

        @PolicyBuilder().retry(max_attempts=10, wait=wait.fixed(0),
                               stop=stop.after_attempt(2))
        def f():
            calls[0] += 1
            raise ValueError("always")

        with pytest.raises(ValueError):
            f()
        assert calls[0] == 2

    def test_retry_if(self):
        calls = [0]

        @PolicyBuilder().retry(max_attempts=5, wait=wait.fixed(0),
                               retry_if=retry_if.exception_type(ValueError))
        def f(kind):
            calls[0] += 1
            raise kind("err")

        with pytest.raises(KeyError):
            f(KeyError)
        assert calls[0] == 1  # KeyError not retried

    def test_fallback(self):
        @PolicyBuilder().retry(max_attempts=1).fallback(lambda: "fb")
        def f():
            raise ValueError("fail")

        assert f() == "fb"

    def test_cache_integration(self):
        calls = [0]

        @PolicyBuilder().cache(ttl=10)
        def f(x):
            calls[0] += 1
            return x + 1

        assert f(1) == 2
        assert f(1) == 2
        assert calls[0] == 1

    def test_event_bus(self):
        bus = EventBus()
        events = []
        bus.subscribe("*", lambda e: events.append(type(e).__name__))

        @PolicyBuilder().retry(max_attempts=1, wait=wait.fixed(0)).observe(event_bus=bus).fallback(lambda: "fb")
        def f():
            raise ValueError("fail")

        f()
        assert any("OperationFailed" in n for n in events)
        assert any("FallbackTriggered" in n for n in events)

    def test_resilient_shortcut(self):
        @resilient(max_attempts=2, wait=wait.fixed(0), fallback=lambda: "safe")
        def f():
            raise ValueError("fail")

        assert f() == "safe"


class TestPolicyBuilderAsync:
    @pytest.mark.asyncio
    async def test_async_retry(self):
        calls = [0]

        @PolicyBuilder().retry(max_attempts=3, wait=wait.fixed(0))
        async def f():
            calls[0] += 1
            if calls[0] < 3:
                raise ValueError("fail")
            return "ok"

        assert await f() == "ok"
        assert calls[0] == 3

    @pytest.mark.asyncio
    async def test_async_fallback(self):
        @PolicyBuilder().retry(max_attempts=1).fallback(lambda: "fb")
        async def f():
            raise ValueError("fail")

        assert await f() == "fb"
