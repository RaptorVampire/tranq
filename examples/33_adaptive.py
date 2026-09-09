"""Example 33: Adaptive resilience controller."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import AdaptiveController

ctrl = AdaptiveController(base_timeout=10.0, base_retry=3,
                          latency_target=0.5, error_target=0.05)

# Simulate healthy operation
for _ in range(20):
    ctrl.observe(latency=0.2, success=True)
print("1) Healthy baseline:", ctrl.recommend())

# Simulate degradation: high latency + errors
for _ in range(20):
    ctrl.observe(latency=2.0, success=False)
rec = ctrl.recommend()
print("2) After degradation:")
print(f"   timeout reduced to {rec['timeout']:.2f}s")
print(f"   retry reduced to   {rec['retry']}")
print(f"   observed latency   {rec['observed_latency']:.2f}s")
print(f"   observed error rate {rec['observed_error_rate']:.2f}")
