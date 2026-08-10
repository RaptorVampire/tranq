import time
import pytest
from tranq import CircuitBreaker, CircuitBreakerError

class TestCircuitBreakerTransitions:
    def test_closed_to_open(self):
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "open"

    def test_open_to_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)
        cb.record_failure()
        assert cb.state == "open"
        time.sleep(0.15)
        assert cb.allow_request()
        assert cb.state == "half-open"

    def test_half_open_to_closed_on_success(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        cb.allow_request()
        cb.record_success()
        assert cb.state == "closed"

    def test_half_open_to_open_on_failure(self):
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        cb.allow_request()
        cb.record_failure()
        assert cb.state == "open"

class TestHalfOpenLimits:
    def test_half_open_requests_limited(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1, half_open_requests=2)
        cb.record_failure()
        time.sleep(0.15)
        assert cb.allow_request()   # 1
        assert cb.allow_request()   # 2
        assert not cb.allow_request()  # 3 denied

    def test_half_open_requests_default_one(self):
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1, half_open_requests=1)
        cb.record_failure()
        time.sleep(0.15)
        assert cb.allow_request()   # 1 allowed (transition)
        assert not cb.allow_request()  # 2 denied

class TestStateProperty:
    def test_state_thread_safe(self):
        import threading
        cb = CircuitBreaker(failure_threshold=5, timeout=10)
        def check():
            for _ in range(10):
                assert cb.state in ("closed", "open", "half-open")
        threads = [threading.Thread(target=check) for _ in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()
