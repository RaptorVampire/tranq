"""Example 13: Function profiling with @profile and @async_profile."""

import sys
import asyncio
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
import tranq.profiling as profiling_module

profiling_module._profiles.clear()

@tranq.profile
def compute_heavy():
    time.sleep(0.02)
    return sum(range(100_000))

@tranq.profile
def compute_light():
    return sum(range(1_000))

@tranq.async_profile
async def async_compute():
    await asyncio.sleep(0.01)
    return "async_done"

# Run multiple times
for _ in range(3):
    compute_heavy()
for _ in range(5):
    compute_light()

asyncio.run(async_compute())
asyncio.run(async_compute())

print("Individual profiles:")
for name in ("compute_heavy", "compute_light", "async_compute"):
    p = tranq.get_profile(name)
    if p:
        print(f"  {name}: calls={p['calls']}, total={p['total_duration']:.4f}s")

print()
print("All profiles:")
for name, p in tranq.get_profile().items():
    print(f"  {name}: {p}")
