import logging
import time
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

class TestHandleSyncBasic:
    def test_no_exception_passes_through(self):
        @handle()
        def f(): return 42
        assert f() == 42

    def test_raises_by_default(self):
        @handle()
        def f(): raise ValueError("boom")
        with pytest.raises(ValueError): f()

    def test_retry_success(self):
        calls = 0
        @handle(on=ValueError, retry=2)
        def f():
            nonlocal calls; calls += 1
            if calls < 3: raise ValueError("fail")
            return "ok"
        assert f() == "ok"; assert calls == 3

    def test_retry_exhausted_raises(self):
        @handle(on=ValueError, retry=1)
        def f(): raise ValueError("boom")
        with pytest.raises(ValueError): f()

    def test_fallback(self):
        @handle(on=ValueError, retry=0, fallback=lambda: "safe", reraise=False)
        def f(): raise ValueError("fail")
        assert f() == "safe"

    def test_reraise_false_returns_none(self):
        @handle(on=ValueError, reraise=False)
        def f(): raise ValueError("fail")
        assert f() is None

class TestHandleSyncAdvanced:
    def test_retry_if_condition(self):
        @handle(on=Exception, retry=2, retry_if=lambda e: "special" in str(e))
        def f(raise_special):
            if raise_special:
                raise ValueError("special error")
            else:
                raise ValueError("normal")
        with pytest.raises(ValueError): f(False)
        with pytest.raises(ValueError): f(True)

    def test_retry_on_result(self):
        results = [None, None, "ok"]
        @handle(retry=2, retry_on_result=lambda r: r is None, reraise=False)
        def f():
            return results.pop(0)
        assert f() == "ok"

    def test_retry_on_result_fails(self):
        @handle(retry=1, retry_on_result=lambda r: r == 0, reraise=False)
        def f(): return 0
        assert f() == 0

    def test_on_error_handler(self):
        handler = MagicMock()
        @handle(on=(ValueError, KeyError), on_error={ValueError: handler}, reraise=False)
        def f(exc): raise exc
        f(ValueError())
        handler.assert_called_once()
        handler.reset_mock()
        f(KeyError())
        handler.assert_not_called()

    def test_metrics(self):
        reset_metrics()
        @handle(metrics=True, metric_prefix="test")
        def f(): return 1
        f()
        metrics = get_metrics()
        assert "test.f" in metrics
        assert metrics["test.f"]["count"] == 1

    def test_circuit_breaker_opens(self):
        cb = CircuitBreaker(failure_threshold=2, timeout=10)
        @handle(on=ValueError, circuit_breaker=cb, retry=0)
        def f(): raise ValueError("fail")
        with pytest.raises(ValueError): f()
        with pytest.raises(ValueError): f()
        with pytest.raises(CircuitBreakerError): f()

    def test_circuit_breaker_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)
        @handle(on=ValueError, circuit_breaker=cb, retry=0)
        def f(): raise ValueError("fail")
        with pytest.raises(ValueError): f()
        with pytest.raises(CircuitBreakerError): f()
        time.sleep(0.15)
        with pytest.raises(ValueError): f()
        with pytest.raises(CircuitBreakerError): f()

    def test_stateful(self):
        counter = 0
        @handle(on=ValueError, retry=2, stateful=True, reraise=False)
        def f():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        assert f() == "ok"
        assert counter == 3

    def test_backoff_strategy(self):
        with patch("time.sleep") as sleep:
            @handle(on=ValueError, retry=3, delay=0.1, backoff_strategy="linear", jitter=False)
            def f(): raise ValueError("fail")
            with pytest.raises(ValueError): f()
            sleep.assert_any_call(pytest.approx(0.1))
            sleep.assert_any_call(pytest.approx(0.2))
            sleep.assert_any_call(pytest.approx(0.3))

    def test_reporters(self):
        mock_reporter = MagicMock()
        @handle(on=ValueError, retry=0, reporters=[mock_reporter])
        def f(): raise ValueError("boom")
        with pytest.raises(ValueError): f()
        assert mock_reporter.report.call_count == 1
        args, kwargs = mock_reporter.report.call_args
        assert isinstance(args[0], ValueError)
        assert args[1]["func"] == "f"

    def test_inject(self):
        @handle(inject={"logger": logging.getLogger("test")})
        def f(logger=None):
            return logger.name
        assert f() == "test"

    def test_retry_if_and_on_result_combined(self):
        side_effects = [ValueError("retry me"), 42]
        call_idx = 0
        @handle(
            on=ValueError,
            retry=1,
            retry_if=lambda e: True,
            reraise=False
        )
        def f():
            nonlocal call_idx
            val = side_effects[call_idx]
            call_idx += 1
            if isinstance(val, Exception):
                raise val
            return val
        assert f() == 42
        assert call_idx == 2
