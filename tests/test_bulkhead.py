import time
import asyncio
import threading
import pytest
from tranq import Bulkhead, AsyncBulkhead, bulkhead, BulkheadFullError


class TestBulkheadCore:
    def test_acquire_release(self):
        bh = Bulkhead(max_concurrent=2, timeout=0)
        assert bh.acquire()
        assert bh.acquire()
        assert not bh.acquire()
        bh.release()
        assert bh.acquire()

    def test_active_count(self):
        bh = Bulkhead(max_concurrent=3, timeout=0)
        bh.acquire()
        bh.acquire()
        assert bh.active == 2
        bh.release()
        assert bh.active == 1


class TestBulkheadDecorator:
    def test_sync_decorator(self):
        @bulkhead(max_concurrent=1, timeout=0)
        def f():
            return "done"
        assert hasattr(f, "bulkhead")
        assert f() == "done"

    def test_raises_when_full(self):
        @bulkhead(max_concurrent=1, timeout=0, raise_on_full=True)
        def g():
            return "x"
        g.bulkhead.acquire()  # پرش کن
        with pytest.raises(BulkheadFullError):
            g()
        g.bulkhead.release()

    def test_async_decorator(self):
        @bulkhead(max_concurrent=1, timeout=0)
        async def f():
            return "async_done"
        assert asyncio.run(f()) == "async_done"

    def test_concurrency_limited(self):
        max_seen = 0
        current = 0
        lock = threading.Lock()

        @bulkhead(max_concurrent=2, timeout=5)
        def work():
            nonlocal current, max_seen
            with lock:
                current += 1
                max_seen = max(max_seen, current)
            time.sleep(0.05)
            with lock:
                current -= 1
            return True

        threads = [threading.Thread(target=work) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert max_seen <= 2
