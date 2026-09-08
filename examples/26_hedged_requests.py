"""Example 26: Hedged requests (async)."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import hedged

attempts = 0


async def slow_backend():
    global attempts
    attempts += 1
    mine = attempts
    delay = 0.5 if mine == 1 else 0.01  # اولی کند، هج‌ها سریع
    await asyncio.sleep(delay)
    return f"result from attempt {mine}"


@hedged(hedge_delay=0.05, max_hedges=3)
async def fetch():
    return await slow_backend()


async def main():
    result = await fetch()
    print(f"Got: {result}")
    print(f"Total backend attempts launched: {attempts}")


asyncio.run(main())
