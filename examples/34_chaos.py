"""Example 34: Chaos / resilience testing framework."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import chaos, chaos_report, reset_chaos_reports

reset_chaos_reports()

print("1) Chaos with 50% error injection:")
successes = failures = 0
with chaos(error_rate=0.5, error_type=ConnectionError, seed=42) as inj:
    for _ in range(20):
        try:
            inj.maybe_inject()
            successes += 1
        except ConnectionError:
            failures += 1

print(f"   successes={successes}, failures={failures}")
print("   injector report:", inj.report())

print()
print("2) Session reports:")
for r in chaos_report():
    print("  ", r)
