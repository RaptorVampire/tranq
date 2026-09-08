"""Example 21: Timeout support for sync and async functions."""
import sys
import time
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq


@tranq.handle(on=Exception, retry=0, timeout=0.2, reraise=False)
def slow_sync():
    time.sleep(2.0)
    return "never"


print("1) Sync timeout (reraise=False -> returns None):")
print("   Result:", repr(slow_sync()))


@tranq.handle(on=Exception, retry=0, timeout=1.0)
def fast_sync():
    return "fast"


print("2) Fast sync unaffected:", fast_sync())


@tranq.handle_async(on=Exception, retry=0, timeout=0.2, reraise=False)
async def slow_async():
    await asyncio.sleep(2.0)
    return "never"


async def main():
    print("3) Async timeout (reraise=False -> returns None):")
    print("   Result:", repr(await slow_async()))


asyncio.run(main())
print("Timeout example completed.")
