"""Example 19: Async decorator @handle_async."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

async def main():
    # Basic async retry
    calls = 0

    @tranq.handle_async(on=ConnectionError, retry=3)
    async def fetch_data():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("network down")
        return {"data": "success"}

    print("1) Async retry:")
    result = await fetch_data()
    print(f"   Result: {result}, calls: {calls}")
    print()

    # Async fallback
    @tranq.handle_async(on=TimeoutError, retry=0,
                        fallback=lambda: {"status": "cached"}, reraise=False)
    async def slow_api():
        raise TimeoutError("timed out")

    print("2) Async fallback:")
    result = await slow_api()
    print(f"   Result: {result}")
    print()

    # Async retry_on_result
    results = [None, "real"]

    @tranq.handle_async(retry=3, retry_on_result=lambda r: r is None, reraise=False)
    async def async_fetch():
        return results.pop(0) if results else None

    print("3) Async retry on result:")
    result = await async_fetch()
    print(f"   Result: {result!r}")
    print()

    # Async on_error
    handled = []

    @tranq.handle_async(on=ValueError, retry=0, reraise=False,
                        on_error={ValueError: lambda e: handled.append(str(e))})
    async def async_value_error():
        raise ValueError("async oops")

    print("4) Async on_error:")
    await async_value_error()
    print(f"   Handled errors: {handled}")

asyncio.run(main())
