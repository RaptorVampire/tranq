"""Example 30: Composable wait strategies and stop conditions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import wait, stop

print("1) Wait strategies:")
for name, w in [
    ("fixed(1.0)", wait.fixed(1.0)),
    ("exponential(0.5, base=2)", wait.exponential(multiplier=0.5, exp_base=2.0)),
    ("fibonacci(0.1)", wait.fibonacci(multiplier=0.1)),
    ("full_jitter(1.0)", wait.full_jitter(multiplier=1.0)),
]:
    print(f"   {name}: attempts 0-3 -> "
          f"{[round(w(i), 3) for i in range(4)]}")

print()
print("2) Stop conditions with AND/OR:")
s_or = stop.after_attempt(3) | stop.after_delay(10.0)
s_and = stop.after_attempt(3) & stop.after_delay(10.0)
print(f"   OR  stop(3 attempts, 1s elapsed)  -> {s_or(3, 1.0)}")
print(f"   AND stop(3 attempts, 1s elapsed)  -> {s_and(3, 1.0)}")
print(f"   AND stop(3 attempts, 11s elapsed) -> {s_and(3, 11.0)}")
