# 🌿 tranq

> **Calm error handling for Python** – decorator-based, zero boilerplate.

<p align="center">
  <a href="https://pypi.org/project/tranq/">
    <img src="https://img.shields.io/badge/PyPI-tranq-blue?style=flat-square" alt="PyPI">
  </a>
  <a href="https://github.com/RaptorVampire/tranq">
    <img src="https://img.shields.io/badge/GitHub-RaptorVampire/tranq-black?style=flat-square" alt="GitHub">
  </a>
  <img src="https://img.shields.io/badge/python-3.9%2B-green?style=flat-square" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/tests-120%2B%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="License">
</p>

---

## 📖 Table of Contents

- [Why tranq?](#-why-tranq)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Features in Depth](#-features-in-depth)
- [Advanced Example](#-advanced-example)
- [API Reference](#-api-reference)
- [Examples](#-examples)
- [Testing](#-testing)
- [Comparison](#-comparison)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧘 Why tranq?

Writing repetitive `try` / `except` blocks clutters your code and hides the business logic.
**tranq** gives you declarative error handling with decorators, context managers, and a rich set of retry strategies – so you can focus on **what** your code does, not **how** it recovers from failures.

| Feature | Description |
|---|---|
| 🧘 **Tranquil** | Clean, readable, and maintainable. |
| 🔁 **Smart retries** | Exponential, linear, Fibonacci backoff, jitter, and max delay. |
| 🚦 **Circuit Breaker** | Prevent cascading failures (sync & async). |
| 🧪 **Conditional retry** | On specific exceptions **or** result values. |
| 📦 **Retry groups** | All-or-nothing execution for multiple functions. |
| 📊 **Built‑in metrics & profiling** | Monitor performance and error rates. |
| 📝 **Pluggable reporters** | Send errors to files (JSON), Sentry, Slack, or custom destinations. |
| 🧩 **Context manager API** | Use `tranq.retry(...)` with all decorator features. |
| 🔧 **Stateful retry** | Persist attempt count across calls (thread/async safe). |
| 🎭 **Mock error injection** | Test your error handling with ease. |
| 💉 **Dependency injection** | Inject dependencies into decorated functions. |
| 🌐 **Global policy** | Set defaults once, override per function. |

---

## 📦 Installation

```bash
pip install tranq
```

> Requires **Python 3.9** or later.

For rich logging output:

```bash
pip install tranq[rich]
```

For development:

```bash
pip install tranq[dev]
```

---

## ⚡ Quick Start

### Decorator (`@handle`)

```python
import tranq

@tranq.handle(on=ValueError, retry=3, delay=0.5, backoff=2.0)
def risky():
    ...
```

### Async (`@handle_async`)

```python
@tranq.handle_async(on=ConnectionError, retry=2, fallback=lambda: "offline")
async def fetch_data():
    ...
```

### Circuit Breaker

```python
cb = tranq.CircuitBreaker(failure_threshold=5, timeout=60)

@tranq.handle(circuit_breaker=cb)
def call_unstable_service():
    ...
```

### Context Manager (full feature parity)

```python
with tranq.retry(on=ValueError, retry=2, retry_if=lambda e: "503" in str(e)) as ctx:
    result = ctx.run(my_function, arg1, arg2)
```

### Retry Group (all‑or‑nothing)

```python
group = tranq.retry_group(step1, step2, step3, on=Exception, retry=1)
results = group.run()  # if any step fails, all are retried together
```

---

## 🔍 Features in Depth

### 1. Retry with Backoff

Choose from **exponential**, **linear**, or **Fibonacci** backoff. Add **jitter** to avoid thundering herds.

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

### 2. Conditional Retry

- `retry_if` – retry only when the exception matches a condition.
- `retry_on_result` – retry if the result is unacceptable (e.g., `None`).

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

### 3. Error Handlers (`on_error`)

Run different callbacks for different exception types.

```python
def log_warning(e):
    print(f"Warning: {e}")

@tranq.handle(
    on=(ValueError, ConnectionError),
    on_error={ValueError: log_warning},
)
def process():
    ...
```

### 4. Circuit Breaker (Sync & Async)

```python
from tranq import CircuitBreaker, AsyncCircuitBreaker

cb = CircuitBreaker(failure_threshold=3, timeout=30, half_open_requests=1)

@tranq.handle(circuit_breaker=cb)
def sync_call():
    ...

acb = AsyncCircuitBreaker(failure_threshold=3, timeout=30)

@tranq.handle_async(circuit_breaker=acb)
async def async_call():
    ...
```

### 5. Stateful Retry (thread‑safe)

Uses `contextvars` to isolate counters, safe for async and threaded code.

```python
@tranq.handle(on=ValueError, retry=3, stateful=True)
def process_item(item):
    ...
```

### 6. Reporters (JSON file, Sentry, Slack)

```python
from tranq import FileReporter, SentryReporter, SlackReporter

reporters = [
    FileReporter("/var/log/tranq_errors.json"),
    SentryReporter(dsn="..."),
    SlackReporter(webhook_url="..."),
]

@tranq.handle(on=Exception, reporters=reporters)
def critical_task():
    ...
```

`FileReporter` writes JSON lines for easier parsing.

### 7. Metrics & Profiling

```python
@tranq.handle(metrics=True, metric_prefix="myapp")
def expensive_op():
    ...

from tranq import get_metrics, profile, get_profile

@profile
def heavy_computation():
    ...

print(get_metrics())
print(get_profile("heavy_computation"))
```

### 8. Mock Error Injection

```python
from tranq import mock_errors

with mock_errors(ValueError, probability=0.8):
    result = my_function()
```

### 9. Dependency Injection

```python
@tranq.handle(inject={"logger": logging.getLogger("app")})
def do_work(logger=None):
    logger.info("Working...")
```

### 10. Global Policy

```python
tranq.set_global_policy(tranq.Policy(
    retry=3,
    delay=0.5,
    backoff=2.0,
    reraise=False,
))

# All @handle calls now inherit these defaults
@tranq.handle(on=ValueError)
def my_func():
    ...
```

---

## 🚀 Advanced Example

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
    reporters=[FileReporter("api_errors.json")],
    fallback=lambda: {"status": "fallback"},
)
def fetch_from_external_api():
    ...
```

---

## 📚 API Reference

### `@tranq.handle(...)` / `@tranq.handle_async(...)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `on` | `type \| tuple` | `Exception` | Exception type(s) to catch |
| `retry` | `int` | `0` | Number of retries (0 = no retry) |
| `delay` | `float` | `0.0` | Base delay between retries (seconds) |
| `backoff` | `float` | `1.0` | Backoff multiplier |
| `backoff_strategy` | `str \| callable` | `"exponential"` | `"exponential"`, `"linear"`, `"fibonacci"`, or custom callable |
| `max_delay` | `float \| None` | `None` | Cap on delay between retries |
| `jitter` | `bool` | `False` | Add ±25% randomness to delays |
| `fallback` | `callable \| None` | `None` | Function to call when all retries fail |
| `reraise` | `bool` | `True` | Re-raise exception after exhaustion |
| `log_level` | `int` | `logging.ERROR` | Logging level for retry messages |
| `message` | `str \| None` | `None` | Custom log format string |
| `policy` | `Policy \| None` | `None` | Explicit policy object |
| `retry_if` | `callable \| None` | `None` | Condition to decide if retry should happen |
| `retry_on_result` | `callable \| None` | `None` | Retry if result matches condition |
| `on_error` | `dict \| None` | `None` | Exception-type → handler mapping |
| `metrics` | `bool` | `False` | Collect metrics for this function |
| `metric_prefix` | `str` | `""` | Prefix for metric keys |
| `circuit_breaker` | `CircuitBreaker \| None` | `None` | Circuit breaker instance |
| `stateful` | `bool` | `False` | Persist attempt count across calls |
| `reporters` | `list \| None` | `None` | List of reporter instances |
| `inject` | `dict \| None` | `None` | Dependencies to inject |

### `tranq.retry(...)` — Context Manager

Same parameters as `@handle`. Usage:

```python
with tranq.retry(on=ValueError, retry=3) as ctx:
    result = ctx.run(my_function, arg1, kwarg1=val)
```

### `tranq.retry_group(...)` / `tranq.async_retry_group(...)`

```python
group = tranq.retry_group(func1, func2, func3, on=Exception, retry=2)
results = group.run()
```

### `tranq.CircuitBreaker(failure_threshold, timeout, half_open_requests)`

### `tranq.AsyncCircuitBreaker(failure_threshold, timeout, half_open_requests)`

### `tranq.mock_errors(exception, probability, seed)`

### `tranq.profile` / `tranq.async_profile`

### `tranq.get_metrics()` / `tranq.reset_metrics()`

### `tranq.get_profile(name=None)`

### `tranq.set_global_policy(policy)` / `tranq.get_global_policy()`

### Exceptions

| Exception | Description |
|---|---|
| `TranqError` | Base exception for all tranq errors |
| `RetryExhaustedError` | All retries exhausted |
| `CircuitBreakerError` | Circuit breaker is open |
| `ResultNotAcceptedError` | Result rejected by `retry_on_result` |
| `RetryGroupError` | Error in a retry group member |

---

## 📁 Examples

The [`examples/`](examples/) directory contains **20 complete, runnable examples** covering every feature:

| File | Topic |
|---|---|
| `01_basic_decorator.py` | Basic `@handle` usage |
| `02_retry_and_backoff.py` | All backoff strategies |
| `03_conditional_retry.py` | `retry_if` |
| `04_retry_on_result.py` | Retry on return value |
| `05_error_handlers.py` | Multiple `on_error` handlers |
| `06_fallback.py` | Fallback values/functions |
| `07_circuit_breaker.py` | Sync circuit breaker |
| `08_async_circuit_breaker.py` | Async circuit breaker |
| `09_context_manager.py` | `with tranq.retry(...)` |
| `10_retry_group.py` | Sync retry group |
| `11_async_retry_group.py` | Async retry group |
| `12_metrics.py` | Metrics collection |
| `13_profiling.py` | Function profiling |
| `14_reporters.py` | File/custom reporters |
| `15_mock_errors.py` | Mock error injection |
| `16_dependency_injection.py` | `inject` parameter |
| `17_stateful_retry.py` | Stateful retry |
| `18_global_policy.py` | Global policy |
| `19_async_decorator.py` | `@handle_async` |
| `20_combined_advanced.py` | Everything combined |

Run all examples:

```bash
python examples/run_all.py
```

Run a single example:

```bash
python examples/07_circuit_breaker.py
```

---

## 🧪 Testing

The [`tests/`](tests/) directory contains a comprehensive test suite with **120+ tests** covering all features:

- Circuit breaker state transitions (sync & async)
- Half-open request limits
- All backoff strategies (exponential, linear, fibonacci, custom)
- Jitter and max_delay
- Conditional retry (`retry_if`, `retry_on_result`)
- Error handlers, fallback, dependency injection
- Stateful retry with thread isolation
- Retry groups (sync & async, mixed sync/async)
- Reporters (FileReporter JSON output)
- Metrics and profiling
- Mock error injection
- Global policy

Run all tests:

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

Run a specific test file:

```bash
pytest tests/test_circuit_breaker.py -v
```

---

## ⚖️ Comparison

| Feature | tranq | tenacity | backoff |
|---|---|---|---|
| Decorator | ✅ | ✅ | ✅ |
| Async support | ✅ | ✅ | ✅ |
| Circuit Breaker | ✅ | ❌ | ❌ |
| Context Manager | ✅ | ❌ | ❌ |
| Retry Groups | ✅ | ❌ | ❌ |
| Metrics | ✅ | ❌ | ❌ |
| Profiling | ✅ | ❌ | ❌ |
| Reporters | ✅ | ❌ | ❌ |
| Mock Errors | ✅ | ❌ | ❌ |
| Dependency Injection | ✅ | ❌ | ❌ |
| Global Policy | ✅ | ❌ | ❌ |
| Stateful Retry | ✅ | ❌ | ❌ |

---

## 🗂️ Project Structure

```
tranq/
├── examples/                    # 20 runnable examples
│   ├── 01_basic_decorator.py
│   ├── ...
│   ├── 20_combined_advanced.py
│   └── run_all.py
├── src/tranq/
│   ├── __init__.py              # Public API
│   ├── decorators.py            # @handle / @handle_async
│   ├── context.py               # retry() context manager
│   ├── circuit_breaker.py       # Sync circuit breaker
│   ├── async_circuit_breaker.py # Async circuit breaker
│   ├── retry_group.py           # Retry groups (sync/async)
│   ├── policies.py              # Policy dataclass
│   ├── exceptions.py            # Custom exceptions
│   ├── metrics.py               # Metrics collection
│   ├── profiling.py             # Function profiling
│   ├── reporters.py             # Error reporters
│   ├── mock.py                  # Mock error injection
│   └── utils.py                 # Backoff, jitter, logging
├── tests/                       # 120+ tests
│   ├── test_circuit_breaker.py
│   ├── test_decorators_sync.py
│   ├── test_decorators_async.py
│   ├── ...
│   └── test_thread_safety.py
├── pyproject.toml
├── pytest.ini
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## 🤝 Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 📄 License

**MIT** © [RaptorVampire](https://github.com/RaptorVampire)