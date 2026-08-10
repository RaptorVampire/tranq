"""Example 18: Global policy and per-call overrides."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

# Set a global policy
tranq.set_global_policy(tranq.Policy(
    retry=2,
    delay=0.05,
    backoff=1.5,
    reraise=False,
))

print("Global policy:", tranq.get_global_policy())

# Functions inherit global policy
calls_a = 0

@tranq.handle(on=ValueError)
def inherits_policy():
    global calls_a
    calls_a += 1
    if calls_a < 3:
        raise ValueError("fail")
    return "ok"

print()
print("1) Function inherits global retry=2:")
result = inherits_policy()
print(f"   Result: {result}, calls: {calls_a}")

# Per-call override
calls_b = 0

@tranq.handle(on=ValueError, retry=5)
def overrides_policy():
    global calls_b
    calls_b += 1
    if calls_b < 4:
        raise ValueError("fail")
    return "ok"

print()
print("2) Function overrides with retry=5:")
result = overrides_policy()
print(f"   Result: {result}, calls: {calls_b}")

# Reset to default
tranq.set_global_policy(tranq.Policy())
print()
print("3) Policy reset to defaults:", tranq.get_global_policy())
