import pytest
from tranq import handle, handle_async


class TestSyncHooks:
    def test_success_hooks(self):
        events = []

        @handle(
            on=ValueError, retry=0,
            on_success=lambda r: events.append(("success", r)),
            on_complete=lambda: events.append(("complete",)),
        )
        def f():
            return "val"

        assert f() == "val"
        assert ("success", "val") in events
        assert ("complete",) in events

    def test_failure_hooks(self):
        events = []

        @handle(
            on=ValueError, retry=0, reraise=False,
            on_failure=lambda e: events.append(("failure", str(e))),
            on_complete=lambda: events.append(("complete",)),
        )
        def f():
            raise ValueError("boom")

        f()
        assert ("failure", "boom") in events
        assert ("complete",) in events

    def test_retry_hook(self):
        retries = []
        calls = 0

        @handle(on=ValueError, retry=2, delay=0,
                on_retry=lambda e, attempt: retries.append(attempt))
        def f():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("fail")
            return "ok"

        assert f() == "ok"
        assert retries == [1, 2]


@pytest.mark.asyncio
class TestAsyncHooks:
    async def test_success_hooks(self):
        events = []

        @handle_async(
            on=ValueError, retry=0,
            on_success=lambda r: events.append(("success", r)),
            on_complete=lambda: events.append(("complete",)),
        )
        async def f():
            return "val"

        assert await f() == "val"
        assert ("success", "val") in events
        assert ("complete",) in events
