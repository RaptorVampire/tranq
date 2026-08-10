"""Example 11: Retry Group — async version (supports mixed sync/async)."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import AsyncCircuitBreaker, CircuitBreakerError

async def main():
    # Mixed sync and async functions
    print("1) Mixed sync/async functions:")

    async def async_step():
        return "async_result"

    def sync_step():
        return "sync_result"

    group = tranq.async_retry_group(async_step, sync_step, on=Exception, retry=0)
    results = await group.run()
    print(f"   Results: {results}")

    # Retry with flaky async
    print()
    print("2) Async retry group with flaky function:")
    attempts = 0

    async def flaky_async():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("network issue")
        return "recovered"

    group = tranq.async_retry_group(
        lambda: "stable",
        flaky_async,
        on=ConnectionError, retry=3
    )
    results = await group.run()
    print(f"   Results: {results}, attempts: {attempts}")

    # With async circuit breaker
    print()
    print("3) Async group with circuit breaker:")
    cb = AsyncCircuitBreaker(failure_threshold=1, timeout=10)

    async def failing():
        raise RuntimeError("down")

    group = tranq.async_retry_group(failing, on=RuntimeError, retry=0, circuit_breaker=cb)
    try:
        await group.run()
    except RuntimeError:
        pass
    try:
        await group.run()
    except CircuitBreakerError as e:
        print(f"   Blocked: {e}")

asyncio.run(main())
