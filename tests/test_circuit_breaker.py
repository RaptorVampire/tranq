import time
from tranq import CircuitBreaker

def test_circuit_breaker_transitions():
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
    assert cb.state == "closed"
    cb.record_failure()
    assert cb.state == "closed"
    cb.record_failure()
    assert cb.state == "open"
    time.sleep(0.15)
    assert cb.allow_request()
    assert cb.state == "half-open"
    cb.record_success()
    assert cb.state == "closed"
