"""Example 28: Statistics, summary table and health report."""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import reset_metrics, summary_table, overall_health, render_report

reset_metrics()
random.seed(7)


@tranq.handle(metrics=True, metric_prefix="svc")
def fast():
    return 1


@tranq.handle(on=ValueError, retry=0, reraise=False, metrics=True, metric_prefix="svc")
def sometimes_fails():
    if random.random() < 0.5:
        raise ValueError("fail")
    return 1


for _ in range(20):
    fast()
for _ in range(20):
    sometimes_fails()

print("Summary table:")
print(summary_table())
print()
print("Overall health:", overall_health())
print()
print("Full report:")
print(render_report())
