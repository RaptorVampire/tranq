import pytest
from tranq import retry_async


@pytest.mark.asyncio
class TestAsyncRetryContext:
    async def test_basic(self):
        calls = 0

        async def f():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("fail")
            return "ok"

        async with retry_async(on=ValueError, retry=3, delay=0) as ctx:
            result = await ctx.run(f)
        assert result == "ok"
        assert calls == 3

    async def test_fallback(self):
        async def f():
            raise ValueError("fail")
        async with retry_async(on=ValueError, retry=0,
                               fallback=lambda: "fb", reraise=False) as ctx:
            result = await ctx.run(f)
        assert result == "fb"

    async def test_reraise(self):
        async def f():
            raise ValueError("fail")
        with pytest.raises(ValueError):
            async with retry_async(on=ValueError, retry=0, reraise=True) as ctx:
                await ctx.run(f)

    async def test_retry_on_result(self):
        results = [None, "ok"]

        async def f():
            return results.pop(0)

        async with retry_async(retry=2, retry_on_result=lambda r: r is None,
                               reraise=False, delay=0) as ctx:
            result = await ctx.run(f)
        assert result == "ok"
