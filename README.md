# tranq

**Calm error handling for Python – decorator-based, zero boilerplate.**

[![PyPI version](https://badge.fury.io/py/tranq.svg)](https://badge.fury.io/py/tranq)
[![Python versions](https://img.shields.io/pypi/pyversions/tranq.svg)](https://pypi.org/project/tranq/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**PyPI:** [https://pypi.org/project/tranq/](https://pypi.org/project/tranq/)  
**GitHub:** [https://github.com/RaptorVampire/tranq](https://github.com/RaptorVampire/tranq)

---

## Why tranq?

Writing repetitive `try/except` blocks clutters your code and hides the business logic. `tranq` gives you **declarative error handling** with decorators, context managers, and a rich set of retry strategies – so you can focus on what your code *does*, not how it recovers from failures.

- 🧘 **Tranquil** – clean, readable, and maintainable.
- 🔁 **Smart retries** – exponential, linear, Fibonacci backoff, jitter, and max delay.
- 🚦 **Circuit Breaker** – prevent cascading failures (sync & async).
- 🧪 **Conditional retry** – on specific exceptions or result values.
- 📦 **Retry groups** – all-or-nothing execution for multiple functions.
- 📊 **Built‑in metrics & profiling** – monitor performance and error rates.
- 📝 **Pluggable reporters** – send errors to files, Sentry, Slack, or custom destinations.
- 🧩 **Context manager API** – use `with tranq.retry(...):` when decorators aren't ideal.
- 🔧 **Stateful retry** – persist attempt count across calls.
- 🎭 **Mock error injection** – test your error handling with ease.

---

## Installation

```bash
pip install tranq
```

Requires Python 3.9 or later.

---

Quick Start

Decorator (@handle)

```python
import tranq

@tranq.handle(on=ValueError, retry=3, delay=0.5, backoff=2.0)
def risky():
    # This will be retried up to 3 times with exponential backoff
    ...
```

Async (@handle_async)

```python
@tranq.handle_async(on=ConnectionError, retry=2, fallback=lambda: "offline")
async def fetch_data():
    ...
```

Circuit Breaker

```python
cb = tranq.CircuitBreaker(failure_threshold=5, timeout=60)
@tranq.handle(circuit_breaker=cb)
def call_unstable_service():
    ...
```

Context Manager

```python
with tranq.retry(on=ValueError, retry=2) as ctx:
    result = ctx.run(my_function, arg1, arg2)
```

Retry Group (all‑or‑nothing)

```python
group = tranq.retry_group(step1, step2, step3, on=Exception, retry=1)
results = group.run()  # if any step fails, all are retried together
```

---

Features in Depth

1. Retry with Backoff

Choose from exponential, linear, or Fibonacci backoff. Add jitter to avoid thundering herds.

```python
@tranq.handle(
    on=TimeoutError,
    retry=5,
    delay=0.1,
    backoff=2.0,
    backoff_strategy="exponential",  # "linear", "fibonacci", or custom callable
    max_delay=10.0,
    jitter=True,
)
def fetch():
    ...
```

2. Conditional Retry

· retry_if – retry only when the exception matches a condition.
· retry_on_result – retry if the result is unacceptable (e.g., None).

```python
@tranq.handle(
    on=requests.RequestException,
    retry_if=lambda e: e.response.status_code == 429,  # rate‑limit
    retry=3,
)
def call_api():
    ...

@tranq.handle(
    retry_on_result=lambda result: result is None,
    retry=2,
)
def get_data():
    ...
```

3. Error Handlers (on_error)

Run different callbacks for different exception types.

```python
def log_warning(e):
    print(f"Warning: {e}")

def alert_admin(e):
    send_alert(e)

@tranq.handle(
    on=(ValueError, ConnectionError),
    on_error={ValueError: log_warning, ConnectionError: alert_admin},
)
def process():
    ...
```

4. Circuit Breaker (Sync & Async)

Prevent repeated calls to a failing service. Available as CircuitBreaker (sync) and AsyncCircuitBreaker (async).

```python
from tranq import CircuitBreaker, AsyncCircuitBreaker

# Sync
cb = CircuitBreaker(failure_threshold=3, timeout=30, half_open_requests=1)
@tranq.handle(circuit_breaker=cb)
def sync_call():
    ...

# Async
acb = AsyncCircuitBreaker(failure_threshold=3, timeout=30)
@tranq.handle_async(circuit_breaker=acb)
async def async_call():
    ...
```

5. Stateful Retry

Persist the attempt counter across multiple invocations – useful for batch processing.

```python
@tranq.handle(on=ValueError, retry=3, stateful=True)
def process_item(item):
    # If it fails, the next call continues from the same attempt number
    ...
```

6. Reporters

Send error details to files, Sentry, Slack, or your own reporter.

```python
from tranq import FileReporter, SentryReporter, SlackReporter

reporters = [
    FileReporter("/var/log/tranq_errors.log"),
    SentryReporter(dsn="..."),
    SlackReporter(webhook_url="..."),
]

@tranq.handle(on=Exception, reporters=reporters)
def critical_task():
    ...
```

Implement your own by subclassing Reporter and defining report(exception, context).

7. Metrics & Profiling

· Metrics: track call count, error count, and total duration (enable with metrics=True).
· Profiling: use the @profile decorator to measure function runtime.

```python
@tranq.handle(metrics=True, metric_prefix="myapp")
def expensive_op():
    ...

from tranq import get_metrics, profile, get_profile

@profile
def heavy_computation():
    ...

print(get_metrics())          # all metric data
print(get_profile("heavy_computation"))  # calls, total_duration
```

8. Mock Error Injection (Testing)

Inject errors with a given probability to test your error‑handling logic.

```python
from tranq import mock_errors

with mock_errors(ValueError, probability=0.8):
    # 80% of the time, ValueError is raised inside this block
    result = my_function()
```

9. Dependency Injection

Pass runtime dependencies directly into your decorated function.

```python
@tranq.handle(inject={"logger": logging.getLogger("app")})
def do_work(logger=None):
    logger.info("Working...")
```

---

Advanced Examples

Combining Features

```python
cb = CircuitBreaker(failure_threshold=3, timeout=60)

@tranq.handle(
    on=requests.RequestException,
    retry=5,
    backoff_strategy="fibonacci",
    max_delay=30,
    jitter=True,
    retry_if=lambda e: e.response.status_code in (429, 503),
    circuit_breaker=cb,
    metrics=True,
    metric_prefix="api",
    reporters=[FileReporter("api_errors.log")],
    fallback=lambda: {"status": "fallback"},
)
def fetch_from_external_api():
    ...
```

Retry Group with Mixed Sync/Async

```python
from tranq import retry_group, async_retry_group

def step1(): ...
def step2(): ...
async def step3(): ...

# Sync group (all functions must be sync)
group = retry_group(step1, step2, on=ValueError, retry=2)
results = group.run()

# Async group – mix sync and async functions
async_group = async_retry_group(step1, step3, on=Exception, retry=1)
results = await async_group.run()
```

---

API Reference

Decorators

· handle(...)
· handle_async(...)

Context Manager

· retry(...)

Retry Groups

· retry_group(*funcs, **kwargs)
· async_retry_group(*funcs, **kwargs)

Circuit Breakers

· CircuitBreaker(failure_threshold, timeout, half_open_requests)
· AsyncCircuitBreaker(...)

Policies

· Policy – dataclass with all configurable parameters.
· set_global_policy(policy) – set a default policy for all decorators.
· get_global_policy()

Reporters

· Reporter (abstract base class)
· FileReporter(file_path)
· SentryReporter(dsn)
· SlackReporter(webhook_url)

Utilities

· get_metrics(), reset_metrics()
· profile(func), get_profile(name=None)
· mock_errors(exception, probability)

Exceptions

· TranqError – base exception.
· RetryExhaustedError – raised when retries are exhausted and reraise=True.
· CircuitBreakerError – raised when circuit is open.
· ResultNotAcceptedError – raised when retry_on_result condition fails.
· RetryGroupError – raised by retry groups on failure.

---

Contributing

Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository.
2. Create a feature branch.
3. Install development dependencies: pip install -e '.[dev]'
4. Run tests: pytest
5. Submit a PR.

For details, see CONTRIBUTING.md.

---

License

MIT © RaptorVampire

---

Acknowledgements

Inspired by libraries like tenacity and backoff, but built with a focus on simplicity, modern Python features, and a consistent API for both sync and async code.

---

Happy error handling! 🧘