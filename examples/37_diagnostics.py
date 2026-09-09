"""Example 37: Automatic health analysis / diagnostics."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import reset_metrics, render_diagnostics, handle

reset_metrics()

@handle(metrics=True, metric_prefix="API")
def api():
    return 1

@handle(on=ValueError, retry=0, reraise=False, metrics=True, metric_prefix="Payment")
def payment():
    raise ValueError("fail")

for _ in range(10):
    api()
for _ in range(10):
    payment()

print(render_diagnostics())
