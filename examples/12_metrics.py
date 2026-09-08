"""Example 12: Built-in metrics collection."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

tranq.reset_metrics()

@tranq.handle(metrics=True, metric_prefix="demo")
def fast_operation():
    return "ok"

@tranq.handle(on=ValueError, retry=0, reraise=False, metrics=True, metric_prefix="demo")
def failing_operation():
    raise ValueError("oops")

@tranq.handle(on=ValueError, retry=2, reraise=False, metrics=True, metric_prefix="demo")
def flaky_operation():
    raise ValueError("flaky")

# Run operations
for _ in range(5):
    fast_operation()
for _ in range(3):
    failing_operation()
for _ in range(2):
    flaky_operation()

metrics = tranq.get_metrics()

print("Collected metrics:")
for name, data in sorted(metrics.items()):
    print(f"  {name}:")
    print(f"    calls:          {data['count']}")
    print(f"    errors:         {data['errors']}")
    print(f"    total_duration: {data['total_duration']:.6f}s")
    if data['count'] > 0:
        print(f"    avg_duration:   {data['total_duration']/data['count']:.6f}s")
    print()

print("Reset metrics:", tranq.reset_metrics() or tranq.get_metrics())
