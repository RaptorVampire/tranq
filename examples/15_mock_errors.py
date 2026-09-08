"""Example 15: Mock error injection for testing."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import mock_errors

def unreliable_function():
    return "real_result"

# 1. Always inject (probability=1.0)
print("1) Probability 1.0 — always raises:")
try:
    with mock_errors(ValueError, probability=1.0):
        unreliable_function()
except ValueError as e:
    print(f"   Injected: {e}")

# 2. Never inject (probability=0.0)
print()
print("2) Probability 0.0 — never raises:")
result = None
with mock_errors(ValueError, probability=0.0):
    result = unreliable_function()
print(f"   Result: {result}")

# 3. Reproducible with seed
print()
print("3) Seeded injection (reproducible):")
try:
    with mock_errors(ConnectionError, probability=0.99, seed=42):
        unreliable_function()
except ConnectionError as e:
    print(f"   Injected with seed 42: {e}")

# 4. Real exceptions pass through
print()
print("4) Real exceptions are not swallowed:")
try:
    with mock_errors(ValueError, probability=0.0):
        raise KeyError("real_error")
except KeyError as e:
    print(f"   Real KeyError passed through: {e}")
