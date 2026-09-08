"""Example 22: Lifecycle event hooks (on_retry / on_success / on_failure / on_complete)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq

events = []


@tranq.handle(
    on=ValueError, retry=2, delay=0,
    on_retry=lambda e, attempt: events.append(f"retry #{attempt}: {e}"),
    on_success=lambda r: events.append(f"success: {r}"),
    on_failure=lambda e: events.append(f"failure: {e}"),
    on_complete=lambda: events.append("complete"),
)
def flaky():
    if not hasattr(flaky, "n"):
        flaky.n = 0
    flaky.n += 1
    if flaky.n < 3:
        raise ValueError(f"attempt {flaky.n} failed")
    return "done"


print("1) Hooks during retry then success:")
print("   Result:", flaky())
for ev in events:
    print("   -", ev)

events.clear()


@tranq.handle(
    on=ValueError, retry=0, reraise=False,
    on_failure=lambda e: events.append(f"failure: {e}"),
    on_complete=lambda: events.append("complete"),
)
def always_fails():
    raise ValueError("boom")


print()
print("2) Hooks on final failure:")
always_fails()
for ev in events:
    print("   -", ev)
