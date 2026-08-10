"""Example 08: Circuit Breaker — async version."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import AsyncCircuitBreaker, CircuitBreakerError

async def main():
    cb = AsyncCircuitBreaker(failure_threshold=2, timeout=0.2, half_open_requests=1)

    @tranq.handle_async(on=RuntimeError, retry=0, circuit_breaker=cb, reraise=True)
    async def unstable_api():
        print("   API called — raising error")
        raise RuntimeError("api down")

    print("1) Fail until circuit opens:")
    for _ in range(2):
        try:
            await unstable_api()
        except RuntimeError:
            pass

    print(f"   State: {await cb.state}")

    print()
    print("2) Circuit OPEN — requests blocked:")
    try:
        await unstable_api()
    except CircuitBreakerError as e:
        print(f"   Blocked: {e}")

    print()
    print("3) Wait for timeout then HALF-OPEN:")
    await asyncio.sleep(0.25)

    @tranq.handle_async(on=RuntimeError, retry=0, circuit_breaker=cb, reraise=True)
    async def success_api():
        print("   Probe succeeded!")

    await success_api()
    print(f"   State after success: {await cb.state}")

asyncio.run(main())
