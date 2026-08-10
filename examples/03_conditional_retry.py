"""Example 03: Conditional retry with retry_if."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

class APIError(Exception):
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}")

call_count = 0

@tranq.handle(
    on=APIError,
    retry=5,
    retry_if=lambda e: e.status_code in (429, 503),
)
def call_api(status_code: int):
    global call_count
    call_count += 1
    print(f"   Attempt {call_count} -> HTTP {status_code}")
    raise APIError(status_code)

# 429 is retried
print("1) Calling with 429 (retriable):")
try:
    call_api(429)
except APIError as e:
    print(f"   Final: {e} after {call_count} attempts")

call_count = 0

# 404 is NOT retried
print()
print("2) Calling with 404 (non-retriable):")
try:
    call_api(404)
except APIError as e:
    print(f"   Final: {e} after {call_count} attempts")
