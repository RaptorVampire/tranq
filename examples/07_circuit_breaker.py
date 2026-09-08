"""Example 07: Circuit Breaker — sync version."""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import CircuitBreaker, CircuitBreakerError

cb = CircuitBreaker(failure_threshold=3, timeout=0.2, half_open_requests=1)

call_count = 0

@tranq.handle(on=RuntimeError, retry=0, circuit_breaker=cb, reraise=True)
def unstable_service():
    global call_count
    call_count += 1
    print(f"   Service called (attempt #{call_count}) — raising error")
    raise RuntimeError("service crashed")

print("1) Normal calls — circuit is CLOSED:")
for _ in range(3):
    try:
        unstable_service()
    except RuntimeError:
        pass

print(f"   State: {cb.state}")

print()
print("2) Circuit is now OPEN — calls rejected immediately:")
try:
    unstable_service()
except CircuitBreakerError as e:
    print(f"   Blocked: {e}")

print()
print("3) Wait for timeout, then HALF-OPEN:")
time.sleep(0.25)
try:
    unstable_service()
except RuntimeError:
    print("   Allowed one probe request — failed again")
    print(f"   State: {cb.state}")

print()
print("4) Success closes the circuit:")
cb2 = CircuitBreaker(failure_threshold=1, timeout=0.1)

@tranq.handle(on=RuntimeError, retry=0, circuit_breaker=cb2, reraise=True)
def probe():
    raise RuntimeError("fail")

try:
    probe()
except RuntimeError:
    pass

print(f"   State after failure: {cb2.state}")
time.sleep(0.15)

@tranq.handle(on=RuntimeError, retry=0, circuit_breaker=cb2, reraise=True)
def success_probe():
    print("   Probe succeeded!")

success_probe()
print(f"   State after success: {cb2.state}")
