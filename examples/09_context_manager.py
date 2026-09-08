"""Example 09: Using tranq.retry as a context manager."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import CircuitBreaker, CircuitBreakerError

# Basic retry
print("1) Basic retry with context manager:")
with tranq.retry(on=ValueError, retry=3) as ctx:
    attempts = [0]

    def flaky():
        attempts[0] += 1
        if attempts[0] < 3:
            raise ValueError("not yet")
        return "done"

    result = ctx.run(flaky)
    print(f"   Result: {result}, attempts: {attempts[0]}")

# With fallback
print()
print("2) With fallback:")
with tranq.retry(on=RuntimeError, retry=0, fallback=lambda: "fallback_value", reraise=False) as ctx:
    def failing():
        raise RuntimeError("oops")
    print(f"   Result: {ctx.run(failing)}")

# With retry_if
print()
print("3) Conditional retry:")
with tranq.retry(on=Exception, retry=2,
                 retry_if=lambda e: "temp" in str(e).lower(),
                 reraise=False) as ctx:
    def temp_error():
        raise Exception("Temporary failure")
    try:
        ctx.run(temp_error)
    except Exception as e:
        print(f"   Retried and raised: {e}")

# With circuit breaker
print()
print("4) With circuit breaker:")
cb = CircuitBreaker(failure_threshold=1, timeout=10)
with tranq.retry(on=ValueError, retry=0, circuit_breaker=cb) as ctx:
    def fail_once():
        raise ValueError("boom")
    try:
        ctx.run(fail_once)
    except ValueError:
        pass
    try:
        ctx.run(fail_once)
    except CircuitBreakerError as e:
        print(f"   Blocked: {e}")

# With dependency injection
print()
print("5) With dependency injection:")
with tranq.retry(inject={"db_name": "postgres"}) as ctx:
    def connect(db_name=None):
        return f"connected to {db_name}"
    print(f"   {ctx.run(connect)}")

# With metrics
print()
print("6) With metrics:")
tranq.reset_metrics()
with tranq.retry(metrics=True, metric_prefix="ctx_demo") as ctx:
    def fast():
        return 42
    ctx.run(fast)
print(f"   Metrics: {tranq.get_metrics()}")