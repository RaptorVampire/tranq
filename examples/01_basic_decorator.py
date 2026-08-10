"""Example 01: Basic usage of @handle decorator."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

# 1. Pass-through: no exception, no retry
@tranq.handle()
def add(a: int, b: int) -> int:
    return a + b

print("1) add(2, 3) =", add(2, 3))


# 2. Exception is re-raised by default
@tranq.handle()
def bad_function():
    raise ValueError("This is not caught by @handle(on=...)")

try:
    bad_function()
except ValueError as e:
    print("2) Caught re-raised ValueError:", e)


# 3. Catch a specific exception and retry
call_count = 0

@tranq.handle(on=ValueError, retry=3)
def flaky_function():
    global call_count
    call_count += 1
    if call_count < 3:
        raise ValueError(f"Attempt {call_count} failed")
    return "success"

print("3) flaky_function() =", flaky_function())
print("   Total calls:", call_count)


# 4. reraise=False: swallow the exception and return None
@tranq.handle(on=KeyError, reraise=False)
def missing_key():
    raise KeyError("missing")

print("4) missing_key() returned:", missing_key())


# 5. Quiet run with high log level
import logging

@tranq.handle(on=ZeroDivisionError, reraise=False, log_level=logging.CRITICAL)
def quiet_divide(a, b):
    return a / b

print("5) quiet_divide(1, 0) =", quiet_divide(1, 0))
