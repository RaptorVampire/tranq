"""Example 17: Stateful retry — attempt counter persists across calls."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

counter = 0

@tranq.handle(on=ValueError, retry=5, stateful=True, reraise=False)
def process_with_memory():
    global counter
    counter += 1
    print(f"   Attempt {counter}...")
    if counter < 4:
        raise ValueError("not yet")
    return "success"

print("1) Stateful retry continues where it left off:")
result = process_with_memory()
print(f"   Result: {result}, total calls: {counter}")
print()

# Without stateful, each call starts from attempt 0
counter2 = 0

@tranq.handle(on=ValueError, retry=1, reraise=False)
def stateless_attempt():
    global counter2
    counter2 += 1
    print(f"   Call {counter2}...")
    raise ValueError("always fails")

print("2) Stateless retry resets each time:")
stateless_attempt()
stateless_attempt()
print(f"   Total calls: {counter2}")
