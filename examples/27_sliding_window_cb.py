"""Example 27: Sliding-window (failure-rate) circuit breaker."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import SlidingWindowCircuitBreaker, CircuitBreakerError

cb = SlidingWindowCircuitBreaker(
    window_size=10, failure_rate_threshold=0.5,
    timeout=0.2, minimum_calls=4, half_open_requests=1)


@tranq.handle(on=RuntimeError, retry=0, circuit_breaker=cb, reraise=True)
def unstable():
    raise RuntimeError("fail")


@tranq.handle(on=RuntimeError, retry=0, circuit_breaker=cb, reraise=True)
def stable():
    return "ok"


print("1) Mixed calls until failure rate >= 50%:")
stable()
stable()
for _ in range(4):
    try:
        unstable()
    except RuntimeError:
        pass
    except CircuitBreakerError:
        break
print(f"   Failure rate: {cb.failure_rate:.2f}, state: {cb.state}")

print()
print("2) Circuit open blocks calls:")
try:
    unstable()
except CircuitBreakerError as e:
    print(f"   Blocked: {e}")

print()
print("3) After timeout, half-open probe succeeds and closes:")
time.sleep(0.25)
print(f"   Probe result: {stable()}, state: {cb.state}")
