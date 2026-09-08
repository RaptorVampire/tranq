import asyncio
import pytest
from tranq import hedged_call, hedged


@pytest.mark.asyncio
class TestHedge:
    async def test_returns_success(self):
        async def ok():
            return "win"
        result = await hedged_call(ok, hedge_delay=0.05, max_hedges=2)
        assert result == "win"

    async def test_recovers_after_failure(self):
        calls = 0

        async def flaky():
            nonlocal calls
            calls += 1
            if calls < 2:
                raise ValueError("first fails")
            return "recovered"

        result = await hedged_call(flaky, hedge_delay=0.01, max_hedges=3)
        assert result == "recovered"

    async def test_all_fail_raises(self):
        async def always_fail():
            raise RuntimeError("nope")
        with pytest.raises(RuntimeError):
            await hedged_call(always_fail, hedge_delay=0.01, max_hedges=2)

    async def test_hedged_decorator(self):
        @hedged(hedge_delay=0.01, max_hedges=2)
        async def f():
            return 42
        assert await f() == 42
