"""Example 23: Rate limiting with a token bucket."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import rate_limit, RateLimitExceeded


@rate_limit(rate=3, per=1.0, burst=3, timeout=0)
def limited_call(i):
    return f"call {i}"


print("1) Burst of 3 allowed, then rejected (timeout=0):")
for i in range(5):
    try:
        print("  ", limited_call(i))
    except RateLimitExceeded as e:
        print(f"   Rejected call {i}: {e}")

print()
print("2) Blocking acquire (waits for tokens):")


@rate_limit(rate=10, per=1.0, burst=2, timeout=2.0)
def wait_call(i):
    return i


start = time.monotonic()
for i in range(4):
    wait_call(i)
print(f"   4 calls at 10/s took {time.monotonic() - start:.3f}s")
