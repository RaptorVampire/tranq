"""Example 25: Retry budget prevents retry storms."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import RetryBudget

budget = RetryBudget(ttl=60, ratio=0.5, min_tokens=2)
for _ in range(10):
    budget.record_call()

print("Budget stats after 10 calls:", budget.stats())
allowed = sum(1 for _ in range(10) if budget.allow_retry())
print(f"Allowed retries out of 10 requests: {allowed} (expected 5)")

calls = 0


@tranq.handle(on=ValueError, retry=5, delay=0,
              retry_budget=RetryBudget(min_tokens=1, ratio=0.0), reraise=False)
def flaky():
    global calls
    calls += 1
    raise ValueError("always fails")


print()
print("With a nearly-empty budget, retries are limited:")
flaky()
print(f"   Function was called {calls} time(s) despite retry=5")
