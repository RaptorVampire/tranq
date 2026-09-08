# 🌿 tranq

> **Calm, production-grade error handling & resilience for Python** — decorator-based, zero boilerplate.

<p align="center">
  <a href="https://pypi.org/project/tranq/"><img src="https://img.shields.io/badge/PyPI-tranq-blue?style=flat-square" alt="PyPI"></a>
  <a href="https://github.com/RaptorVampire/tranq"><img src="https://img.shields.io/badge/GitHub-RaptorVampire/tranq-black?style=flat-square" alt="GitHub"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-green?style=flat-square" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/tests-135%2B%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="License">
  ![CI](https://github.com/RaptorVampire/tranq/actions/workflows/ci.yml/badge.svg)
  ![PyPI](https://img.shields.io/pypi/v/tranq)
  ![Python](https://img.shields.io/pypi/pyversions/tranq)
</p>

---

## 🧘 Why tranq?

Writing repetitive `try`/`except` blocks clutters your code and hides business logic.
**tranq** gives you declarative error handling *and* a full resilience toolkit — retries,
circuit breakers, rate limits, bulkheads, hedging, timeouts, budgets, metrics and more —
so you focus on **what** your code does, not **how** it recovers from failure.

| Feature | Description |
|---|---|
| 🔁 **Smart retries** | Exponential / linear / Fibonacci backoff, jitter, max delay |
| ⏱️ **Timeouts** | Hard execution limits for sync & async functions |
| 🚦 **Circuit Breaker** | Count-based *and* sliding-window (failure-rate), sync & async |
| 🚦 **Rate Limiter** | Token-bucket throttling (`@rate_limit`) |
| 🚪 **Bulkhead** | Concurrency isolation (`@bulkhead`) |
| 🏇 **Hedged requests** | Race duplicate async requests, take the first success |
| 💰 **Retry budget** | Prevent retry storms under load |
| 🪝 **Event hooks** | `on_retry` / `on_success` / `on_failure` / `on_complete` |
| 📊 **Metrics** | Counts, error-rate and **p50 / p95 / p99** latencies |
| 📈 **Statistics** | Summary tables & health reports |
| 📝 **Reporters** | File (JSON), Log, Sentry, Slack, Prometheus |
| 🧩 **Context managers** | `tranq.retry(...)` and `async with tranq.retry_async(...)` |
| 📦 **Retry groups** | All-or-nothing execution for multiple functions |
| 🔧 **Stateful retry** | Persist attempt count across calls (thread/async safe) |
| 🎭 **Mock errors** | Inject exceptions for testing |
| 💉 **Dependency injection** | Inject dependencies into decorated functions |
| 🌐 **Global policy** | Set defaults once, override per function |

---

## 📦 Installation

```bash
pip install tranq
```

Optional integrations:

```bash
pip install tranq[rich]         # pretty logging
pip install tranq[sentry]       # Sentry reporter
pip install tranq[slack]        # Slack reporter
pip install tranq[prometheus]   # Prometheus reporter
pip install tranq[all]          # everything
```

---

## ⚡ Quick Start

```python
import tranq

@tranq.handle(on=ConnectionError, retry=3, delay=0.5, backoff=2.0, timeout=5.0)
def fetch():
    ...

@tranq.handle_async(on=TimeoutError, retry=2, fallback=lambda: "offline")
async def fetch_async():
    ...
```

---

## 🔍 Features in Depth

### Retry with Backoff
```python
@tranq.handle(on=TimeoutError, retry=5, delay=0.1, backoff=2.0,
              backoff_strategy="exponential", max_delay=10.0, jitter=True)
def fetch(): ...
```

### Timeout
```python
@tranq.handle(on=Exception, retry=2, timeout=3.0)   # raises FunctionTimeoutError
def slow(): ...
```

### Event Hooks
```python
@tranq.handle(on=ValueError, retry=3,
              on_retry=lambda e, n: print(f"retry {n}"),
              on_success=lambda r: print("ok"),
              on_failure=lambda e: print("failed"),
              on_complete=lambda: print("done"))
def work(): ...
```

### Circuit Breaker (count-based & sliding-window)
```python
cb  = tranq.CircuitBreaker(failure_threshold=5, timeout=60)
swc = tranq.SlidingWindowCircuitBreaker(window_size=100,
                                        failure_rate_threshold=0.5,
                                        minimum_calls=10)

@tranq.handle(circuit_breaker=swc)
def call_service(): ...
```

### Rate Limiter
```python
@tranq.rate_limit(rate=10, per=1.0, burst=20)
def api_call(): ...
```

### Bulkhead
```python
@tranq.bulkhead(max_concurrent=5, timeout=1.0)
def limited(): ...
```

### Retry Budget
```python
budget = tranq.RetryBudget(ttl=60, ratio=0.2, min_tokens=10)

@tranq.handle(on=Exception, retry=5, retry_budget=budget)
def protected(): ...
```

### Hedged Requests (async)
```python
@tranq.hedged(hedge_delay=0.1, max_hedges=2)
async def fast_fetch(): ...
```

### Async Context Manager
```python
async with tranq.retry_async(on=ConnectionError, retry=3) as ctx:
    result = await ctx.run(my_async_func, arg)
```

### Metrics & Statistics
```python
@tranq.handle(metrics=True, metric_prefix="svc")
def op(): ...

print(tranq.summary_table())      # aligned table with p50/p95/p99
print(tranq.overall_health())     # {'status': 'healthy', ...}
```

### Reporters
```python
reporters = [
    tranq.FileReporter("errors.jsonl"),
    tranq.LogReporter(),
    tranq.SentryReporter(dsn="..."),
    tranq.SlackReporter(webhook_url="..."),
    tranq.PrometheusReporter(),
]

@tranq.handle(on=Exception, reporters=reporters)
def critical(): ...
```

---

## 📚 API Reference

### Decorators
- `tranq.handle(on, retry, delay, backoff, backoff_strategy, max_delay, jitter, fallback, reraise, log_level, message, policy, retry_if, retry_on_result, on_error, metrics, metric_prefix, circuit_breaker, stateful, reporters, inject, timeout, on_retry, on_success, on_failure, on_complete, retry_budget)`
- `tranq.handle_async(...)` — same parameters for `async def`.

### Standalone decorators
- `tranq.rate_limit(rate, per=1.0, burst=None, timeout=None, raise_on_limit=True)`
- `tranq.bulkhead(max_concurrent, timeout=None, raise_on_full=True)`
- `tranq.hedged(hedge_delay=0.1, max_hedges=2)`
- `tranq.profile` / `tranq.async_profile`

### Context managers
- `tranq.retry(...)` → `ctx.run(func, *args, **kwargs)`
- `tranq.retry_async(...)` → `async with` + `await ctx.run(...)`

### Circuit breakers
- `tranq.CircuitBreaker(failure_threshold, timeout, half_open_requests)` + `.reset()`
- `tranq.AsyncCircuitBreaker(...)` + `.reset()`
- `tranq.SlidingWindowCircuitBreaker(window_size, failure_rate_threshold, timeout, half_open_requests, minimum_calls)`
- `tranq.AsyncSlidingWindowCircuitBreaker(...)`

### Resilience primitives
- `tranq.RateLimiter(rate, per, burst)` / `.acquire()` / `.acquire_async()`
- `tranq.Bulkhead(max_concurrent, timeout)` / `tranq.AsyncBulkhead(...)`
- `tranq.RetryBudget(ttl, ratio, min_tokens)` / `.allow_retry()` / `.record_call()`
- `tranq.hedged_call(func, args, kwargs, hedge_delay, max_hedges)`

### Metrics & statistics
- `tranq.get_metrics()` → count, errors, total/avg/min/max, error_rate, p50/p95/p99
- `tranq.reset_metrics()`
- `tranq.summary_table()` / `tranq.overall_health()` / `tranq.render_report()`
- `tranq.get_profile(name=None)`

### Global policy
- `tranq.set_global_policy(tranq.Policy(...))` / `tranq.get_global_policy()`

### Exceptions
| Exception | Meaning |
|---|---|
| `TranqError` | Base class |
| `RetryExhaustedError` | Retries exhausted |
| `CircuitBreakerError` | Circuit open |
| `ResultNotAcceptedError` | `retry_on_result` rejected final result |
| `RetryGroupError` | Retry group member failed |
| `FunctionTimeoutError` | `timeout` exceeded (also a builtin `TimeoutError`) |
| `RateLimitExceeded` | Rate limiter rejected the call |
| `BulkheadFullError` | Bulkhead at capacity |
| `RetryBudgetExhaustedError` | Retry budget empty |

---

## 📁 Examples

The [`examples/`](examples/) directory contains **29 runnable examples** (01–29)
covering every feature, including the new ones: timeouts, hooks, rate limiting,
bulkheads, retry budgets, hedging, sliding-window breakers, statistics and
`retry_async`.

```bash
python examples/run_all.py
```

---

## 🧪 Testing

The suite contains **135+ tests** (sync, async, thread-safety).

```bash
pip install pytest "pytest-asyncio>=0.24"
pytest tests/ -v
```

---

## ⚖️ Comparison

| Feature | tranq | tenacity | backoff |
|---|---|---|---|
| Decorator + Async | ✅ | ✅ | ✅ |
| Circuit Breaker | ✅ | ❌ | ❌ |
| Sliding-window breaker | ✅ | ❌ | ❌ |
| Rate Limiter | ✅ | ❌ | ❌ |
| Bulkhead | ✅ | ❌ | ❌ |
| Retry Budget | ✅ | ❌ | ❌ |
| Hedged Requests | ✅ | ❌ | ❌ |
| Timeouts | ✅ | ⚠️ | ❌ |
| Event Hooks | ✅ | ⚠️ | ❌ |
| Context Manager | ✅ | ❌ | ❌ |
| Retry Groups | ✅ | ❌ | ❌ |
| Metrics + percentiles | ✅ | ❌ | ❌ |
| Reporters | ✅ | ❌ | ❌ |

---

## 🤝 Contributing

Contributions are welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## 📄 License

**MIT** © [RaptorVampire](https://github.com/RaptorVampire)
