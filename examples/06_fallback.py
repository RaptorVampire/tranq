"""Example 06: Fallback values and functions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

# Static fallback via lambda
@tranq.handle(on=RuntimeError, retry=0, fallback=lambda: "cached_value", reraise=False)
def get_live_data():
    raise RuntimeError("service down")

print("1) Static fallback:", get_live_data())

# Fallback receives the same arguments
@tranq.handle(on=ZeroDivisionError, retry=0,
              fallback=lambda a, b: float("inf") if b == 0 else a / b,
              reraise=False)
def safe_divide(a, b):
    return a / b

print("2) Argument-aware fallback:", safe_divide(10, 0))

# Fallback after retries are exhausted
attempts = 0

@tranq.handle(on=ValueError, retry=2, fallback=lambda: "default_after_retries", reraise=False)
def flaky_with_fallback():
    global attempts
    attempts += 1
    print(f"   Attempt {attempts}...")
    raise ValueError("still failing")

print("3) Fallback after retries:")
result = flaky_with_fallback()
print(f"   Result: {result!r}")

# Fallback with reraise=True still calls fallback before raising
@tranq.handle(on=ValueError, retry=0, fallback=lambda: "fb", reraise=True)
def fails_with_fallback():
    raise ValueError("boom")

print("4) Fallback with reraise=True:")
try:
    fails_with_fallback()
except ValueError:
    print("   Exception was raised after fallback returned")
