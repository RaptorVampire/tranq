"""Example 04: Retry when the return value is unacceptable."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import ResultNotAcceptedError

results_queue = [None, None, "real_data"]

@tranq.handle(
    retry=5,
    retry_on_result=lambda result: result is None,
    reraise=False,
)
def fetch_data():
    value = results_queue.pop(0) if results_queue else None
    print(f"   fetch_data() -> {value!r}")
    return value

print("1) Retry until non-None result:")
data = fetch_data()
print(f"   Final result: {data!r}")
print()

# Exhausted: always returns None
@tranq.handle(retry=2, retry_on_result=lambda r: r is None, reraise=False)
def always_none():
    print("   always_none() -> None")
    return None

print("2) Result never accepted, reraise=False:")
result = always_none()
print(f"   Final result: {result!r}")
print()

# With reraise=True, ResultNotAcceptedError is raised
@tranq.handle(retry=1, retry_on_result=lambda r: r == 0, reraise=True)
def returns_zero():
    return 0

print("3) Result never accepted, reraise=True:")
try:
    returns_zero()
except ResultNotAcceptedError as e:
    print(f"   Caught: {type(e).__name__}: {e}")
