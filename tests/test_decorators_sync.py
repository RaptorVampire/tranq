import time
import logging
from unittest.mock import patch, MagicMock
import pytest
from tranq import (
    handle, set_global_policy, Policy,
    CircuitBreaker, CircuitBreakerError, ResultNotAcceptedError,
    get_metrics, reset_metrics, FileReporter
)

@pytest.fixture(autouse=True)
def reset_state():
    reset_metrics()
    set_global_policy(Policy())
    yield

class TestBasic:
    def test_pass_through(self):
        @handle()
        def f(): return 42
        assert f() == 42

    def test_default_reraise(self):
        @handle()
        def f(): raise ValueError("boom")
        with pytest.raises(ValueError): f()

    def test_retry_success(self):
        calls = 0
        @handle(on=ValueError, retry=3)
        def f():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert f() == "ok"
        assert calls == 3

    def test_fallback(self):
        @handle(on=ValueError, retry=0, fallback=lambda: "safe", reraise=False)
        def f(): raise ValueError("fail")
        assert f() == "safe"

    def test_reraise_false(self):
        @handle(on=ValueError, reraise=False)
        def f(): raise ValueError("fail")
        assert f() is None

class TestRetryIf:
    def test_retry_if_true(self):
        @handle(on=Exception, retry=2, retry_if=lambda e: "retry" in str(e))
        def f(msg): raise Exception(msg)
        with pytest.raises(Exception): f("normal")
        with pytest.raises(Exception): f("retry me")

class TestRetryOnResult:
    def test_retry_on_result(self):
        results = [None, None, "ok"]
        @handle(retry=2, retry_on_result=lambda r: r is None, reraise=False)
        def f(): return results.pop(0)
        assert f() == "ok"

    def test_retry_on_result_exhausted(self):
        @handle(retry=1, retry_on_result=lambda r: r == 0, reraise=True)
        def f(): return 0
        with pytest.raises(ResultNotAcceptedError): f()

class TestOnError:
    def test_on_error_called(self):
        called = []
        @handle(on=ValueError, on_error={ValueError: lambda e: called.append(1)}, reraise=False)
        def f(): raise ValueError("oops")
        f()
        assert len(called) == 1

    def test_on_error_not_called_for_other(self):
        called = []
        @handle(on=(ValueError, KeyError), on_error={ValueError: lambda e: called.append(1)}, reraise=False)
        def f(exc): raise exc
        f(KeyError())
        assert len(called) == 0

class TestCircuitBreaker:
    def test_opens(self):
        cb = CircuitBreaker(failure_threshold=2, timeout=10)
        @handle(on=ValueError, circuit_breaker=cb, retry=0)
        def f(): raise ValueError("fail")
        with pytest.raises(ValueError): f()
        with pytest.raises(ValueError): f()
        with pytest.raises(CircuitBreakerError): f()

    def test_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)
        @handle(on=ValueError, circuit_breaker=cb, retry=0)
        def f(): raise ValueError("fail")
        with pytest.raises(ValueError): f()
        with pytest.raises(CircuitBreakerError): f()
        time.sleep(0.15)
        with pytest.raises(ValueError): f()
        with pytest.raises(CircuitBreakerError): f()

class TestStateful:
    def test_stateful(self):
        counter = 0
        @handle(on=ValueError, retry=2, stateful=True, reraise=False)
        def f():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        assert f() == "ok"
        assert counter == 3

class TestBackoffStrategies:
    def test_linear(self):
        with patch("time.sleep") as sleep:
            @handle(on=ValueError, retry=3, delay=0.1, backoff_strategy="linear", jitter=False)
            def f(): raise ValueError("fail")
            with pytest.raises(ValueError): f()
            sleep.assert_any_call(pytest.approx(0.1))
            sleep.assert_any_call(pytest.approx(0.2))
            sleep.assert_any_call(pytest.approx(0.3))

    def test_fibonacci(self):
        delays = []
        import time as _time
        orig = _time.sleep
        _time.sleep = lambda t: delays.append(t)
        try:
            @handle(on=ValueError, retry=5, delay=0.1, backoff_strategy="fibonacci", jitter=False)
            def f(): raise ValueError("fail")
            with pytest.raises(ValueError): f()
            expected = [0.1, 0.1, 0.2, 0.3, 0.5]
            for i, (d, e) in enumerate(zip(delays, expected)):
                assert abs(d - e) < 0.01
        finally:
            _time.sleep = orig

    def test_exponential(self):
        delays = []
        import time as _time
        orig = _time.sleep
        _time.sleep = lambda t: delays.append(t)
        try:
            @handle(on=ValueError, retry=3, delay=0.1, backoff=2.0, backoff_strategy="exponential", jitter=False)
            def f(): raise ValueError("fail")
            with pytest.raises(ValueError): f()
            expected = [0.1, 0.2, 0.4]
            for i, (d, e) in enumerate(zip(delays, expected)):
                assert abs(d - e) < 0.01
        finally:
            _time.sleep = orig

    def test_custom_callable(self):
        delays = []
        import time as _time
        orig = _time.sleep
        _time.sleep = lambda t: delays.append(t)
        try:
            @handle(on=ValueError, retry=3, delay=1.0, backoff_strategy=lambda a: a*2.0, jitter=False)
            def f(): raise ValueError("fail")
            with pytest.raises(ValueError): f()
            assert delays == [0.0, 2.0, 4.0]
        finally:
            _time.sleep = orig

class TestJitterAndMaxDelay:
    def test_jitter_range(self):
        delays = []
        import time as _time
        orig = _time.sleep
        _time.sleep = lambda t: delays.append(t)
        try:
            @handle(on=ValueError, retry=5, delay=1.0, jitter=True, backoff_strategy=lambda a: 1.0)
            def f(): raise ValueError("fail")
            with pytest.raises(ValueError): f()
            for d in delays:
                assert 0.75 <= d <= 1.25
        finally:
            _time.sleep = orig

    def test_max_delay(self):
        delays = []
        import time as _time
        orig = _time.sleep
        _time.sleep = lambda t: delays.append(t)
        try:
            @handle(on=ValueError, retry=3, delay=1.0, backoff=10.0, max_delay=2.0, jitter=False)
            def f(): raise ValueError("fail")
            with pytest.raises(ValueError): f()
            for d in delays:
                assert d <= 2.0
        finally:
            _time.sleep = orig

class TestReporters:
    def test_reporter_called(self):
        reports = []
        class R:
            def report(self, e, ctx): reports.append(e)
        @handle(on=ValueError, retry=0, reporters=[R()])
        def f(): raise ValueError("boom")
        with pytest.raises(ValueError): f()
        assert len(reports) == 1

class TestInject:
    def test_inject(self):
        @handle(inject={"logger": logging.getLogger("test_inject")})
        def f(logger=None): return logger.name
        assert f() == "test_inject"

class TestMetrics:
    def test_metrics_count(self):
        reset_metrics()
        @handle(metrics=True, metric_prefix="t1")
        def f(): return 1
        f()
        m = get_metrics()
        assert m["t1.f"]["count"] == 1

    def test_metrics_errors(self):
        reset_metrics()
        @handle(on=ValueError, retry=0, reraise=False, metrics=True, metric_prefix="err")
        def f(): raise ValueError("fail")
        f()
        m = get_metrics()
        assert m["err.f"]["errors"] == 1
