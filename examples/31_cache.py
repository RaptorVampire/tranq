"""Example 31: Resilience cache with TTL, stampede prevention, stale-if-error."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import cache, TranqCache

calls = 0

@cache(ttl=5)
def expensive(x):
    global calls
    calls += 1
    return x * 10

print("1) Cache-aside decorator:")
print("   expensive(5) =", expensive(5))
print("   expensive(5) =", expensive(5), "(cached)")
print("   underlying calls:", calls)

print()
print("2) Stale-if-error via PolicyBuilder:")
store = TranqCache(ttl=0.05, stale_if_error=True)
store.set("key", "fresh_value")
time.sleep(0.06)
hit, stale = store.get_stale("key")
print(f"   stale value served after TTL: {stale!r}")

print()
print("3) Cache metrics:")
print("  ", expensive.cache.metrics())
