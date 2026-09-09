"""Example 32: Policy composition DSL (PolicyBuilder)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import PolicyBuilder, wait, stop, retry_if, EventBus

bus = EventBus()
bus.subscribe("*", lambda e: print(f"   [event] {type(e).__name__}"))

policy = (
    PolicyBuilder()
    .retry(max_attempts=3, wait=wait.fixed(0.01),
           retry_if=retry_if.exception_type(ConnectionError))
    .timeout(2.0)
    .fallback(lambda: {"status": "fallback"})
    .observe(event_bus=bus)
)

calls = 0

@policy
def fetch():
    global calls
    calls += 1
    if calls < 3:
        raise ConnectionError("down")
    return {"status": "ok"}

print("1) PolicyBuilder with retry + timeout + fallback + events:")
print("   result:", fetch())
print("   calls:", calls)

print()
print("2) Fallback path:")
calls = 100  # force exhaustion

@PolicyBuilder().retry(max_attempts=1, wait=wait.fixed(0)).fallback(lambda: "fb")
def always_down():
    raise ConnectionError("never works")

print("   result:", always_down())
