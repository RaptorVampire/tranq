import pytest
from tranq import retry

def test_context_retry_basic():
    with retry(on=ValueError, retry=2) as ctx:
        calls = 0
        def f():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert ctx.run(f) == "ok"

def test_context_retry_fallback():
    with retry(on=ValueError, retry=0, fallback=lambda: 42) as ctx:
        def f(): raise ValueError()
        assert ctx.run(f) == 42
