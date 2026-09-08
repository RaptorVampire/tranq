"""Example 24: Bulkhead concurrency limiting."""
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import bulkhead

max_concurrent = 0
current = 0
lock = threading.Lock()


@bulkhead(max_concurrent=2, timeout=5)
def work(i):
    global current, max_concurrent
    with lock:
        current += 1
        max_concurrent = max(max_concurrent, current)
    time.sleep(0.1)
    with lock:
        current -= 1
    return i


threads = [threading.Thread(target=work, args=(i,)) for i in range(6)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Max concurrent observed: {max_concurrent} (limit was 2)")
assert max_concurrent <= 2
print("Bulkhead example completed.")
