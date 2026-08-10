"""Example 10: Retry Group — all-or-nothing execution (sync)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import CircuitBreaker, CircuitBreakerError

# All succeed
print("1) All functions succeed:")
group = tranq.retry_group(
    lambda: "step1",
    lambda: "step2",
    lambda: "step3",
    on=Exception, retry=0
)
print(f"   Results: {group.run()}")

# Retry until all succeed
print()
print("2) Retry group with flaky function:")
attempts = [0]

def flaky_step():
    attempts[0] += 1
    if attempts[0] < 3:
        raise ValueError("flaky")
    return "flaky_ok"

group = tranq.retry_group(
    lambda: "stable",
    flaky_step,
    on=ValueError, retry=3
)
print(f"   Results: {group.run()}")
print(f"   Total flaky attempts: {attempts[0]}")

# All-or-nothing: one failure re-runs everything
print()
print("3) All-or-nothing behavior:")
run_counts = {"a": 0, "b": 0}

def step_a():
    run_counts["a"] += 1
    return "a"

def step_b():
    run_counts["b"] += 1
    if run_counts["b"] < 2:
        raise RuntimeError("b failed on first try")
    return "b"

group = tranq.retry_group(step_a, step_b, on=RuntimeError, retry=2, reraise=False)
print(f"   Results: {group.run()}")
print(f"   step_a ran {run_counts['a']} times (re-ran because step_b failed)")

# Fallback for the whole group
print()
print("4) Group fallback:")

def always_fails():
    raise RuntimeError("fail")

group = tranq.retry_group(
    always_fails,
    on=RuntimeError, retry=0,
    fallback=lambda: ["group_fallback"],
    reraise=False
)
print(f"   Results: {group.run()}")

# With circuit breaker
print()
print("5) Group with circuit breaker:")
cb = CircuitBreaker(failure_threshold=1, timeout=10)

def fails_with_cb():
    raise ValueError("fail")

group = tranq.retry_group(fails_with_cb, on=ValueError, retry=0, circuit_breaker=cb)
try:
    group.run()
except ValueError:
    pass
try:
    group.run()
except CircuitBreakerError as e:
    print(f"   Blocked: {e}")