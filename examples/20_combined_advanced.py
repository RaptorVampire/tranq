"""Example 20: Combining all features in a realistic scenario."""

import sys
import time
import json
import tempfile
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq
from tranq import CircuitBreaker, FileReporter

tranq.reset_metrics()

# Setup
log_path = tempfile.mktemp(suffix=".json")
cb = CircuitBreaker(failure_threshold=3, timeout=0.3, half_open_requests=1)
reporter = FileReporter(log_path)

class ExternalService:
    """Simulates an unreliable external API."""
    def __init__(self):
        self.call_count = 0

    def fetch(self, resource: str):
        self.call_count += 1
        print(f"      Service call #{self.call_count}: {resource}")

        # First 2 calls: rate limited (retriable)
        if self.call_count <= 2:
            raise ConnectionError("429 Too Many Requests")

        # Next call: server error (retriable)
        if self.call_count == 3:
            raise ConnectionError("503 Service Unavailable")

        # After that: success
        return {"resource": resource, "data": "payload"}

service = ExternalService()

@tranq.handle(
    on=ConnectionError,
    retry=5,
    delay=0.05,
    backoff=2.0,
    backoff_strategy="exponential",
    max_delay=1.0,
    jitter=False,
    retry_if=lambda e: "429" in str(e) or "503" in str(e),
    circuit_breaker=cb,
    metrics=True,
    metric_prefix="external_api",
    reporters=[reporter],
    fallback=lambda resource: {"resource": resource, "data": "FALLBACK"},
    reraise=False,
)
def fetch_resource(resource: str):
    return service.fetch(resource)

print("1) Fetch with full retry pipeline:")
result = fetch_resource("users/42")
print(f"   Final result: {result}")
print(f"   Circuit state: {cb.state}")
print(f"   Service was called {service.call_count} times")
print()

print("2) Metrics collected:")
for name, data in tranq.get_metrics().items():
    print(f"   {name}: {data}")

print()
print("3) Error log written by FileReporter:")
if os.path.exists(log_path):
    with open(log_path) as f:
        for line in f:
            record = json.loads(line)
            print(f"   {record['exception_type']}: {record['exception_message']}")
    os.unlink(log_path)

print()
print("4) Fallback scenario — service always fails:")
service2 = ExternalService()

@tranq.handle(
    on=ConnectionError,
    retry=2,
    delay=0.01,
    retry_if=lambda e: True,
    fallback=lambda: {"data": "CACHED_FALLBACK"},
    reraise=False,
)
def always_fails():
    raise ConnectionError("500 Internal Server Error")

result = always_fails()
print(f"   Result: {result}")

print()
print("5) Circuit breaker opens after repeated failures:")
cb2 = CircuitBreaker(failure_threshold=2, timeout=0.2)

@tranq.handle(on=RuntimeError, retry=0, circuit_breaker=cb2, reraise=True)
def doomed():
    raise RuntimeError("doomed")

for _ in range(2):
    try:
        doomed()
    except RuntimeError:
        pass

print(f"   Circuit state: {cb2.state}")
try:
    doomed()
except tranq.CircuitBreakerError as e:
    print(f"   Blocked: {e}")

print()
print("Combined example completed.")
