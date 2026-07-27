import pytest
import asyncio
from tranq import retry_group, async_retry_group

def step1():
    return 1

def step2():
    return 2

def step3_fail():
    raise ValueError("fail")

class TestRetryGroupSync:
    def test_all_success(self):
        group = retry_group(step1, step2, on=Exception, retry=0)
        results = group.run()
        assert results == [1, 2]

    def test_one_fails_retry(self):
        call_count = 0
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"
        group = retry_group(step1, flaky, on=ValueError, retry=2)
        results = group.run()
        assert results == [1, "ok"]
        assert call_count == 3

    def test_fail_exhausted(self):
        group = retry_group(step3_fail, on=ValueError, retry=1, reraise=False)
        assert group.run() is None

@pytest.mark.asyncio
class TestRetryGroupAsync:
    async def test_all_success_async(self):
        async def async_step1():
            return 1
        async def async_step2():
            return 2
        group = async_retry_group(async_step1, async_step2, on=Exception, retry=0)
        results = await group.run()
        assert results == [1, 2]

    async def test_one_fails_retry_async(self):
        call_count = 0
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"
        group = async_retry_group(step1, flaky, on=ValueError, retry=2)
        results = await group.run()
        assert results == [1, "ok"]
        assert call_count == 3

    async def test_fail_exhausted_async(self):
        async def failing():
            raise ValueError("fail")
        group = async_retry_group(failing, on=ValueError, retry=1, reraise=False)
        assert await group.run() is None
