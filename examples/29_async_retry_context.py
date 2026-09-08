"""Example 29: Async context manager retry_async."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import retry_async


async def main():
    calls = 0

    async def flaky():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("down")
        return "connected"

    async with retry_async(on=ConnectionError, retry=4, delay=0) as ctx:
        result = await ctx.run(flaky)
    print(f"Result: {result}, attempts: {calls}")

    async def always_down():
        raise ConnectionError("down")

    async with retry_async(on=ConnectionError, retry=0,
                           fallback=lambda: "offline", reraise=False) as ctx:
        result = await ctx.run(always_down)
    print(f"Fallback result: {result}")


asyncio.run(main())
