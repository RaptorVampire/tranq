import time
import asyncio
import pytest
from tranq import handle, handle_async, FunctionTimeoutError


class TestSyncTimeout:
    def test_timeout_raises(self):
        @handle(on=Exception, retry=0, timeout=0.05, reraise=True)
        def slow():
            time.sleep(0.3)
            return "done"
        with pytest.raises(FunctionTimeoutError):
            slow()

    def test_no_timeout_when_fast(self):
        @handle(on=Exception, retry=0, timeout=1.0)
        def fast():
            return "quick"
        assert fast() == "quick"

    def test_timeout_is_timeouterror(self):
        @handle(on=TimeoutError, retry=0, timeout=0.05, reraise=True)
        def slow():
            time.sleep(0.3)
        with pytest.raises(TimeoutError):
            slow()


@pytest.mark.asyncio
class TestAsyncTimeout:
    async def test_timeout_raises(self):
        @handle_async(on=Exception, retry=0, timeout=0.05, reraise=True)
        async def slow():
            await asyncio.sleep(0.3)
            return "done"
        with pytest.raises(FunctionTimeoutError):
            await slow()

    async def test_no_timeout_when_fast(self):
        @handle_async(on=Exception, retry=0, timeout=1.0)
        async def fast():
            return "quick"
        assert await fast() == "quick"
