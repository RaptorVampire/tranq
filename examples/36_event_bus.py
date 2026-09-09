"""Example 36: Unified event bus for resilience events."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import EventBus, CircuitBreaker
from tranq import events
from tranq import PolicyBuilder, wait

bus = EventBus()
log = []
bus.subscribe("*", lambda e: log.append(type(e).__name__))

cb = CircuitBreaker(failure_threshold=2, timeout=10, event_bus=bus, name="db")

@PolicyBuilder().retry(max_attempts=1, wait=wait.fixed(0)).circuit_breaker(cb).fallback(lambda: "fb")
def flaky():
    raise RuntimeError("boom")

print("1) Trigger failures to open the circuit:")
for _ in range(3):
    flaky()

print("   circuit state:", cb.state)
print("   events captured:", log)
