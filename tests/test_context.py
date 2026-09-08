import pytest
from unittest.mock import MagicMock
from tranq import retry, CircuitBreaker, CircuitBreakerError, get_metrics, reset_metrics

def test_basic_retry():
    with retry(on=ValueError, retry=2) as ctx:
        calls = 0
        def f():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert ctx.run(f) == "ok"

def test_fallback():
    with retry(on=ValueError, retry=0, fallback=lambda: 42) as ctx:
        assert ctx.run(lambda: exec('raise ValueError()')) == 42

def test_retry_if():
    with retry(on=Exception, retry=1, retry_if=lambda e: "retry" in str(e)) as ctx:
        with pytest.raises(Exception): ctx.run(lambda: exec('raise Exception("normal")'))
        with pytest.raises(Exception): ctx.run(lambda: exec('raise Exception("retry me")'))

def test_retry_on_result():
    results = [None, "ok"]
    with retry(retry=1, retry_on_result=lambda r: r is None, reraise=False) as ctx:
        def f(): return results.pop(0)
        assert ctx.run(f) == "ok"

def test_on_error():
    called = []
    with retry(on=ValueError, on_error={ValueError: lambda e: called.append(1)}, reraise=False) as ctx:
        ctx.run(lambda: exec('raise ValueError("oops")'))
    assert len(called) == 1

def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=1, timeout=10)
    with retry(on=ValueError, circuit_breaker=cb, retry=0) as ctx:
        with pytest.raises(ValueError): ctx.run(lambda: exec('raise ValueError("fail")'))
        with pytest.raises(CircuitBreakerError): ctx.run(lambda: exec('raise ValueError("fail")'))

def test_stateful():
    counter = 0
    with retry(on=ValueError, retry=2, stateful=True, reraise=False) as ctx:
        def f():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        assert ctx.run(f) == "ok"
    assert counter == 3

def test_reporters():
    reports = []
    class R:
        def report(self, e, ctx): reports.append(e)
    with retry(on=ValueError, retry=0, reporters=[R()]) as ctx:
        with pytest.raises(ValueError): ctx.run(lambda: exec('raise ValueError("boom")'))
    assert len(reports) == 1

def test_inject():
    with retry(inject={"db": "postgres"}) as ctx:
        def f(db=None): return db
        assert ctx.run(f) == "postgres"

def test_metrics():
    reset_metrics()
    with retry(metrics=True, metric_prefix="ctx") as ctx:
        def f(): return 42
        assert ctx.run(f) == 42
    m = get_metrics()
    assert "ctx.f" in m
    assert m["ctx.f"]["count"] == 1

def test_backoff_linear():
    delays = []
    import time as _time
    orig = _time.sleep
    _time.sleep = lambda t: delays.append(t)
    try:
        with retry(on=ValueError, retry=2, delay=0.1, backoff_strategy="linear", jitter=False) as ctx:
            with pytest.raises(ValueError):
                ctx.run(lambda: exec('raise ValueError("fail")'))
        assert len(delays) == 2
        assert abs(delays[0] - 0.1) < 0.01
        assert abs(delays[1] - 0.2) < 0.01
    finally:
        _time.sleep = orig
