# 🌿 tranq

> **Calm, production-grade error handling & resilience for Python** — decorator-based, zero boilerplate, battle-tested.

<p align="center">
  <a href="https://pypi.org/project/tranq/">
    <img src="https://img.shields.io/pypi/v/tranq?style=for-the-badge&color=blue" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/tranq/">
    <img src="https://img.shields.io/pypi/pyversions/tranq?style=for-the-badge&color=green" alt="Python Versions">
  </a>
  <a href="https://github.com/RaptorVampire/tranq/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/RaptorVampire/tranq/ci.yml?style=for-the-badge&label=CI" alt="CI Status">
  </a>
  <a href="https://pypi.org/project/tranq/">
    <img src="https://img.shields.io/pypi/l/tranq?style=for-the-badge&color=orange" alt="License">
  </a>
  <a href="https://github.com/RaptorVampire/tranq">
    <img src="https://img.shields.io/badge/GitHub-RaptorVampire%2Ftranq-black?style=for-the-badge" alt="GitHub">
  </a>
</p>

<p align="center">
  <strong>
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-features">Features</a> •
    <a href="#-api-reference">API Reference</a> •
    <a href="#-examples">Examples</a> •
    <a href="#-comparison">Comparison</a> •
    <a href="#-installation">Installation</a>
  </strong>
</p>

---

## 🧘 Why tranq?

Writing repetitive `try`/`except` blocks clutters your code and buries business logic under layers of defensive programming. Retry loops, circuit breakers, rate limits, and timeout handling are **cross-cutting concerns** that should not pollute your core logic.

**tranq** gives you **declarative error handling** through decorators, context managers, and a comprehensive resilience toolkit — so you focus on **what** your code does, not **how** it recovers from failure.

```python
# ❌ Without tranq: 30+ lines of boilerplate
import time, logging
for attempt in range(5):
    try:
        result = call_external_api()
        break
    except ConnectionError as e:
        if attempt == 4: raise
        logging.warning(f"Attempt {attempt+1} failed: {e}")
        time.sleep(2 ** attempt)

# ✅ With tranq: 2 lines
import tranq

@tranq.handle(on=ConnectionError, retry=4, delay=1.0, backoff=2.0)
def call_external_api():
    ...
```

### Design Principles

| Principle | Description |
|---|---|
| 🧘 **Tranquil** | Clean, readable, maintainable. Zero boilerplate. |
| 🔌 **Non-invasive** | Decorators and context managers. No code changes inside functions. |
| 🧩 **Composable** | Every feature combines: retry + CB + timeout + metrics + hooks. |
| 🏭 **Production-ready** | Thread-safe, async-safe, contextvar-isolated. 190+ tests. |
| 📦 **Zero dependencies** | Core has no external deps. Optional extras for integrations. |
| 🔍 **Observable** | Built-in metrics, profiling, percentiles, health reports, reporters. |

---

## ⚡ Quick Start

### Decorator (`@handle`)

```python
import tranq

@tranq.handle(on=ValueError, retry=3, delay=0.5, backoff=2.0)
def risky_operation():
    """Retried up to 3 times on ValueError with exponential backoff."""
    ...
```

### Async Decorator (`@handle_async`)

```python
@tranq.handle_async(on=ConnectionError, retry=2, fallback=lambda: "offline")
async def fetch_data():
    """Async function with fallback on failure."""
    ...
```

### Circuit Breaker

```python
cb = tranq.CircuitBreaker(failure_threshold=5, timeout=60)

@tranq.handle(on=Exception, circuit_breaker=cb)
def call_unstable_service():
    ...
```

### Context Manager (Sync)

```python
with tranq.retry(on=ValueError, retry=2, delay=0.1) as ctx:
    result = ctx.run(my_function, arg1, kwarg1=value)
```

### Async Context Manager

```python
async with tranq.retry_async(on=ConnectionError, retry=3) as ctx:
    result = await ctx.run(my_async_function, arg1)
```

### Policy Composition DSL

```python
from tranq import PolicyBuilder, wait, stop, retry_if

policy = (
    PolicyBuilder()
    .retry(max_attempts=3, wait=wait.exponential(0.5, max=10))
    .timeout(5)
    .circuit_breaker(tranq.SlidingWindowCircuitBreaker(failure_rate_threshold=0.5))
    .rate_limit(rate=10)
    .bulkhead(max_concurrent=5)
    .fallback(lambda: {"status": "cached"})
    .cache(ttl=60)
)

@policy
def call_service():
    ...
```

### Rate Limiter

```python
@tranq.rate_limit(rate=10, per=1.0, burst=20)
def api_call():
    """Limited to 10 calls/second with burst of 20."""
    ...
```

### Bulkhead (Concurrency Limit)

```python
@tranq.bulkhead(max_concurrent=5, timeout=10.0)
def limited_operation():
    """At most 5 concurrent executions."""
    ...
```

### Retry Group (All-or-Nothing)

```python
group = tranq.retry_group(step1, step2, step3, on=Exception, retry=2)
results = group.run()  # All steps retried together if any fails
```

---

## 📦 Installation

```bash
pip install tranq
```

> Requires **Python 3.9** or later. The library has **zero runtime dependencies**.

### Optional Extras

```bash
pip install tranq[rich]         # Pretty terminal logging with colors
pip install tranq[sentry]       # Sentry error reporting
pip install tranq[slack]        # Slack webhook notifications
pip install tranq[prometheus]   # Prometheus metrics exposition
pip install tranq[all]          # All integrations
pip install tranq[dev]          # Development tools (pytest, black, isort, build, twine)
```

Verify installation:

```bash
python -m tranq
# Output: tranq v1.1.0 - Calm error handling with advanced resilience features.
```

---

## 🔥 Features

### Layer 1 — Competitor Parity

#### 🔁 Smart Retries
Exponential, linear, Fibonacci, constant, random backoff. Full/equal/decorrelated jitter. Custom callable. Min/max delay cap. Composable with `+`.

```python
from tranq import wait, stop

@tranq.handle(
    on=TimeoutError,
    retry=5,
    delay=0.1,
    backoff=2.0,
    backoff_strategy="exponential",
    max_delay=10.0,
    jitter=True,
)
def fetch(): ...
```

#### ⏱️ Timeouts
Hard execution limits for sync & async functions. Per-attempt and total-operation deadlines.

```python
@tranq.handle(on=Exception, retry=2, timeout=5.0)
def slow_operation(): ...
```

#### 🚦 Circuit Breakers
Count-based and sliding-window (failure-rate). Slow-call detection. State-change events. Breaker registry. Sync & async.

```python
swc = tranq.SlidingWindowCircuitBreaker(
    window_size=100, failure_rate_threshold=0.5, minimum_calls=10)

@tranq.handle(on=Exception, circuit_breaker=swc)
def unreliable_service(): ...
```

#### 🚦 Rate Limiting
Token bucket, leaky bucket, fixed window, sliding window, adaptive rate limiting.

```python
@tranq.rate_limit(rate=10, per=1.0, burst=20)
def api_call(): ...
```

#### 🚪 Bulkhead Isolation
Thread-based, async semaphore, queue-based, per-key isolation.

```python
@tranq.bulkhead(max_concurrent=5, timeout=10.0)
def database_query(): ...
```

#### 💰 Retry Budget
Prevents retry storms under load.

```python
budget = tranq.RetryBudget(ttl=60, ratio=0.2, min_tokens=10)

@tranq.handle(on=Exception, retry=5, retry_budget=budget)
def protected_call(): ...
```

#### 🏇 Hedged Requests
Race duplicate async requests, take the first success. Quorum mode. Percentile-based delay.

```python
@tranq.hedged(hedge_delay=0.1, max_hedges=2)
async def fast_fetch(): ...
```

#### 🧪 Conditional Retry
Retry on specific exceptions, result values, HTTP status codes, exception chains, or Retry-After headers.

```python
from tranq import retry_if

@tranq.handle(
    on=Exception,
    retry=3,
    retry_if=retry_if.http_status((429, 503)) | retry_if.exception_type(ConnectionError),
)
def call_api(): ...
```

#### 📝 Reporters
File (JSON lines), Log, Sentry, Slack, Prometheus. Pluggable custom reporters.

```python
reporters = [
    tranq.FileReporter("errors.jsonl"),
    tranq.LogReporter(),
    tranq.SentryReporter(dsn="..."),
    tranq.SlackReporter(webhook_url="..."),
    tranq.PrometheusReporter(),
]

@tranq.handle(on=Exception, reporters=reporters)
def critical_operation(): ...
```

#### 🎭 Mock Error Injection
Inject exceptions for testing with configurable probability and seed.

```python
with tranq.mock_errors(ConnectionError, probability=0.8, seed=42):
    result = my_function()
```

#### 💉 Dependency Injection
Inject dependencies into decorated functions.

```python
@tranq.handle(inject={"logger": logging.getLogger("app")})
def do_work(logger=None):
    logger.info("Working...")
```

#### 🌐 Global Policy
Set defaults once, override per function.

```python
tranq.set_global_policy(tranq.Policy(retry=3, delay=0.5, backoff=2.0))
```

---

### Layer 2 — What Makes tranq Different

#### 🧠 Adaptive Resilience
Automatically tunes policy based on observed latency, error rate, and traffic.

```python
ctrl = tranq.AdaptiveController(base_timeout=10.0, base_retry=3)
ctrl.observe(latency=2.0, success=False)
rec = ctrl.recommend()
# {'timeout': 2.5, 'retry': 1, 'observed_error_rate': 1.0, ...}
```

#### 🎯 Policy Presets
Ready-made configs for common backends.

```python
from tranq import presets

@tranq.resilient(**presets.http())
def fetch_users(): ...

@tranq.resilient(**presets.database())
def run_query(): ...

# Available: http, database, redis, kafka, queue, grpc, llm
```

#### 🌐 HTTP Intelligence
Automatic retryable status detection and Retry-After parsing.

```python
from tranq import is_retryable, parse_retry_after, recommended_wait

if is_retryable(exception):
    wait_seconds = recommended_wait(exception, default=1.0)
```

#### 🔭 OpenTelemetry Native
Automatic spans and counters for resilience operations. Graceful no-op when not installed.

```python
@tranq.telemetry(service="payment")
def process_payment(): ...
```

#### 📡 Unified Event Bus
Subscribe to 14 resilience lifecycle events.

```python
bus = tranq.EventBus()
bus.subscribe(tranq.events.CircuitOpened, lambda e: alert(f"CB opened: {e.data}"))
bus.subscribe("*", lambda e: log(e))  # wildcard
```

Events: `RetryStarted`, `RetryCompleted`, `CircuitOpened`, `CircuitClosed`, `CircuitHalfOpened`, `TimeoutTriggered`, `RateLimitExceeded`, `BulkheadRejected`, `FallbackTriggered`, `CacheHit`, `CacheMiss`, `HedgeStarted`, `OperationSucceeded`, `OperationFailed`.

#### 🧬 Distributed Resilience
Pluggable state backends (in-memory, Redis) for cluster-wide rate limits, circuit breakers, and budgets.

```python
from tranq import RedisBackend, DistributedRateLimiter

backend = RedisBackend(url="redis://localhost:6379/0")
limiter = DistributedRateLimiter(limit=100, window=1.0, backend=backend)
```

#### 🕸️ Dependency-Aware Resilience
Track health of named dependencies and aggregate service health.

```python
graph = tranq.DependencyGraph()
graph.register("api", dependencies=["postgres", "redis", "payment"])
graph.record("payment", success=False)
print(graph.failing_dependencies("api"))  # ["payment"]
```

#### 🩺 Automatic Health Analysis
Full resilience diagnostics with recommended actions.

```python
print(tranq.render_diagnostics())
# SERVICE HEALTH
# ────────────────────────────────
# API                  HEALTHY
# Payment              DEGRADED
# Overall: DEGRADED (calls=500, errors=12)
# Recommended actions:
#   - Enable jitter to avoid thundering herds
#   - A circuit breaker is open; investigate downstream
```

#### 🧪 Chaos Testing Framework
Inject latency, errors, and timeouts for resilience testing.

```python
with tranq.chaos(latency=0.3, error_rate=0.2, timeout_rate=0.1) as inj:
    for _ in range(100):
        inj.maybe_inject()
        call_service()

print(tranq.chaos_report())
```

#### 🧩 Policy Composition DSL
Fluent builder composing all resilience features into a single decorator.

```python
from tranq import PolicyBuilder, wait, stop, retry_if

policy = (
    PolicyBuilder()
    .retry(max_attempts=3, wait=wait.full_jitter(0.5, max=10),
           stop=stop.after_attempt(3) | stop.after_delay(30))
    .timeout(5)
    .circuit_breaker(tranq.SlidingWindowCircuitBreaker(...))
    .rate_limit(rate=10)
    .bulkhead(max_concurrent=5)
    .fallback(tranq.FallbackChain(cached_fallback, static_fallback))
    .cache(ttl=60)
    .observe(event_bus=bus)
)

@policy
def call_service(): ...
```

#### 🤖 LLM Resilience
Rate-limit handling, Retry-After, provider/model fallback, automatic failover.

```python
@tranq.llm(max_attempts=5, providers=[anthropic_client, local_model])
async def ask(prompt): ...
```

#### 🏆 Auto Policy Detection
Detect operation type and recommend/apply a policy automatically.

```python
@tranq.auto(verbose=True)  # Recommends only (safe by default)
async def fetch_orders(): ...

@tranq.auto(apply=True)    # Actually applies the recommended policy
async def fetch_users(): ...
```

#### 📊 Advanced Metrics & Statistics
Counts, error-rate, min/max/avg, **p50/p95/p99** latencies, summary tables, health reports.

```python
@tranq.handle(metrics=True, metric_prefix="svc")
def expensive_op(): ...

print(tranq.summary_table())
print(tranq.overall_health())
```

#### 🗄️ Resilience Cache
TTL, LRU eviction, stampede prevention (single-flight), stale-if-error, negative caching, cache metrics.

```python
@tranq.cache(ttl=60, maxsize=256)
def expensive_computation(x): ...
```

#### 🔄 Fallback Strategies
Static, callable, async, chain, cached (stale-while-failing), conditional.

```python
chain = tranq.FallbackChain(cached_result, redis_fallback, static_default)

@PolicyBuilder().fallback(chain)
def get_data(): ...
```

---

## 📚 API Reference

### Decorators

| Function | Description |
|---|---|
| `@tranq.handle(...)` | Sync decorator with full error handling |
| `@tranq.handle_async(...)` | Async decorator (same parameters) |
| `@tranq.rate_limit(rate, per, burst, timeout)` | Token-bucket rate limiter |
| `@tranq.bulkhead(max_concurrent, timeout)` | Concurrency limiter |
| `@tranq.hedged(hedge_delay, max_hedges)` | Hedged requests (async) |
| `@tranq.profile` / `@tranq.async_profile` | Execution time measurement |
| `@tranq.cache(ttl, maxsize)` | Cache-aside decorator |
| `@tranq.telemetry(service)` | OpenTelemetry spans |
| `@tranq.llm(max_attempts, providers)` | LLM resilience |
| `@tranq.auto(apply, verbose)` | Auto policy detection |
| `@tranq.resilient(...)` | Shortcut for PolicyBuilder |

### Context Managers

| Function | Description |
|---|---|
| `tranq.retry(...)` | Sync context manager |
| `tranq.retry_async(...)` | Async context manager |

### Retry Primitives

| Module | Key Classes/Functions |
|---|---|
| `tranq.wait` | `fixed`, `none`, `random`, `exponential`, `fibonacci`, `incrementing`, `full_jitter`, `equal_jitter`, `decorrelate_jitter`, `combine` |
| `tranq.stop` | `after_attempt`, `after_delay`, `before_deadline`, `never`, `when`, `all` (`&`), `any` (`\|`) |
| `tranq.retry_if` | `exception_type`, `not_exception_type`, `exception`, `result`, `http_status`, `exception_chain`, `retry_after`, `all` (`&`), `any` (`\|`) |

### Circuit Breakers

| Class | Description |
|---|---|
| `CircuitBreaker` | Count-based sync (+ slow-call, events, reset) |
| `AsyncCircuitBreaker` | Count-based async |
| `SlidingWindowCircuitBreaker` | Failure-rate sync |
| `AsyncSlidingWindowCircuitBreaker` | Failure-rate async |
| `BreakerRegistry` | Shared named breakers |

### Rate Limiters

| Class | Algorithm |
|---|---|
| `RateLimiter` | Token bucket |
| `LeakyBucket` | Leaky bucket |
| `FixedWindowLimiter` | Fixed window counter |
| `SlidingWindowLimiter` | Sliding window log |
| `AdaptiveRateLimiter` | Auto-adjusting token bucket |
| `DistributedRateLimiter` | Cluster-wide fixed window |

### Bulkheads

| Class | Description |
|---|---|
| `Bulkhead` | Thread semaphore |
| `AsyncBulkhead` | Asyncio semaphore |
| `QueueBulkhead` | Bounded queue + worker pool |
| `KeyedBulkhead` | Per-key isolation |

### Other Components

| Component | Description |
|---|---|
| `RetryBudget` | Token-based retry storm prevention |
| `TranqCache` / `AsyncTranqCache` | TTL + LRU + stampede prevention |
| `FallbackChain` | Sequential fallback attempts |
| `CachedFallback` | Stale-while-failing |
| `ConditionalFallback` | Exception-type-based fallback |
| `EventBus` | Pub/sub for 14 event types |
| `AdaptiveController` | Auto-tuning from observed signals |
| `DependencyGraph` | Dependency health tracking |
| `ChaosInjector` | Latency/error/timeout injection |
| `Telemetry` | OpenTelemetry integration |
| `Deadline` | Absolute deadline with propagation |
| `PolicyBuilder` | Fluent policy composition |
| `presets` | http/database/redis/kafka/grpc/llm |

### Exceptions

| Exception | Description |
|---|---|
| `TranqError` | Base class |
| `RetryExhaustedError` | All retries exhausted |
| `CircuitBreakerError` | Circuit breaker open |
| `ResultNotAcceptedError` | `retry_on_result` rejected final result |
| `RetryGroupError` | Retry group member failed |
| `FunctionTimeoutError` | Timeout exceeded (also `TimeoutError`) |
| `RateLimitExceeded` | Rate limiter rejected call |
| `BulkheadFullError` | Bulkhead at capacity |
| `RetryBudgetExhaustedError` | Retry budget empty |
| `DeadlineExceededError` | Overall deadline passed |

### Utilities

| Function | Description |
|---|---|
| `get_metrics()` / `reset_metrics()` | Metrics collection |
| `summary_table()` / `overall_health()` / `render_report()` | Statistics |
| `diagnostics()` / `render_diagnostics()` | Health analysis |
| `chaos(...)` / `chaos_report()` | Chaos testing |
| `mock_errors(...)` | Error injection |
| `set_global_policy()` / `get_global_policy()` | Global defaults |
| `is_retryable()` / `parse_retry_after()` | HTTP intelligence |
| `recommend_policy()` | Auto policy detection |

---

## 📁 Examples

The [`examples/`](examples/) directory contains **38 complete, runnable scripts**:

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
| `21_timeout.py` | Sync/async timeout |
| `22_event_hooks.py` | Lifecycle hooks |
| `23_rate_limiter.py` | Token bucket rate limiting |
| `24_bulkhead.py` | Concurrency isolation |
| `25_retry_budget.py` | Retry storm prevention |
| `26_hedged_requests.py` | Hedged async requests |
| `27_sliding_window_cb.py` | Failure-rate circuit breaker |
| `28_statistics_report.py` | Summary tables & health |
| `29_async_retry_context.py` | `async with tranq.retry_async` |
| `30_wait_stop.py` | Composable wait/stop |
| `31_cache.py` | Cache with stampede prevention |
| `32_policy_builder.py` | Policy composition DSL |
| `33_adaptive.py` | Adaptive resilience |
| `34_chaos.py` | Chaos testing |
| `35_presets.py` | Policy presets |
| `36_event_bus.py` | Unified event bus |
| `37_diagnostics.py` | Health analysis |
| `38_auto_llm.py` | Auto detection & LLM resilience |

```bash
python examples/run_all.py       # Run all 38 examples
python examples/07_circuit_breaker.py  # Run a single example
```

---

## 🧪 Testing

The test suite contains **190+ tests** covering all features across sync, async, and thread-safety:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Test categories: circuit breakers (count + sliding window), all backoff strategies, jitter, conditional retry, error handlers, fallback, dependency injection, stateful retry, retry groups, reporters, metrics, profiling, mock errors, global policy, timeout, event hooks, rate limiters (5 algorithms), bulkhead, retry budget, hedged requests, cache, chaos testing, presets, diagnostics, event bus, wait/stop/retry_if composition, policy builder.

---

## ⚖️ Comparison

| Feature | **tranq** | tenacity | backoff | pyresilience |
|---|---|---|---|---|
| Decorator (sync + async) | ✅ | ✅ | ✅ | ✅ |
| Circuit Breaker | ✅ | ❌ | ❌ | ✅ |
| Sliding Window CB | ✅ | ❌ | ❌ | ❌ |
| Rate Limiter (5 algorithms) | ✅ | ❌ | ❌ | ✅ |
| Bulkhead (4 types) | ✅ | ❌ | ❌ | ✅ |
| Retry Budget | ✅ | ❌ | ❌ | ✅ |
| Hedged Requests | ✅ | ❌ | ❌ | ❌ |
| Timeout | ✅ | ⚠️ | ❌ | ✅ |
| Event Hooks | ✅ | ⚠️ | ⚠️ | ❌ |
| Context Manager | ✅ | ❌ | ❌ | ❌ |
| Async Context Manager | ✅ | ❌ | ❌ | ❌ |
| Retry Groups | ✅ | ❌ | ❌ | ❌ |
| Metrics + Percentiles | ✅ | ❌ | ❌ | ✅ |
| Statistics / Health | ✅ | ❌ | ❌ | ❌ |
| Reporters (5 built-in) | ✅ | ❌ | ❌ | ❌ |
| Mock Errors / Chaos | ✅ | ❌ | ❌ | ❌ |
| Dependency Injection | ✅ | ❌ | ❌ | ❌ |
| Global Policy | ✅ | ❌ | ❌ | ❌ |
| Stateful Retry | ✅ | ❌ | ❌ | ❌ |
| Cache + Stampede Prevention | ✅ | ❌ | ❌ | ✅ |
| Policy Composition DSL | ✅ | ❌ | ❌ | ❌ |
| Adaptive Resilience | ✅ | ❌ | ❌ | ❌ |
| Policy Presets | ✅ | ❌ | ❌ | ✅ |
| HTTP Intelligence | ✅ | ❌ | ❌ | ✅ |
| OpenTelemetry Native | ✅ | ❌ | ❌ | ❌ |
| Event Bus | ✅ | ❌ | ❌ | ❌ |
| Distributed State | ✅ | ❌ | ❌ | ❌ |
| Dependency Graph | ✅ | ❌ | ❌ | ❌ |
| LLM Resilience | ✅ | ❌ | ❌ | ✅ |
| Auto Policy Detection | ✅ | ❌ | ❌ | ❌ |
| Zero Dependencies | ✅ | ✅ | ✅ | ❌ |

---

## 🗂️ Project Structure

```
tranq/
├── .github/workflows/
│   ├── ci.yml                    # Test matrix (5 Python × 3 OS)
│   └── release.yml              # Auto-publish to PyPI + GitHub Release
├── docs/source/
│   ├── conf.py
│   └── index.rst                # Full Sphinx documentation
├── examples/                     # 38 runnable examples
│   ├── 01_basic_decorator.py
│   ├── ...
│   ├── 38_auto_llm.py
│   └── run_all.py
├── src/tranq/
│   ├── __init__.py              # Public API (101 exports)
│   ├── __main__.py              # python -m tranq
│   ├── decorators.py            # @handle / @handle_async
│   ├── context.py               # retry() / retry_async()
│   ├── composition.py           # PolicyBuilder / ResiliencePolicy
│   ├── circuit_breaker.py       # Count-based CB + slow-call + registry
│   ├── async_circuit_breaker.py # Async count-based CB
│   ├── sliding_window.py        # Failure-rate CB (sync + async)
│   ├── rate_limiter.py          # 5 rate limiting algorithms
│   ├── bulkhead.py              # 4 bulkhead types
│   ├── retry_budget.py          # Retry storm prevention
│   ├── hedge.py                 # Hedged requests + quorum
│   ├── cache.py                 # TTL/LRU/stampede/stale-if-error
│   ├── fallback.py              # Chain/cached/conditional fallback
│   ├── wait.py                  # 10 composable wait strategies
│   ├── stop.py                  # Composable stop conditions
│   ├── retry_predicates.py      # Composable retry predicates
│   ├── timeout.py               # Deadline + per-attempt timeout
│   ├── events.py                # Unified event bus (14 events)
│   ├── adaptive.py              # Adaptive resilience controller
│   ├── presets.py               # http/db/redis/kafka/grpc/llm
│   ├── http_intel.py            # HTTP status + Retry-After
│   ├── diagnostics.py           # Health analysis + recommendations
│   ├── chaos.py                 # Chaos testing framework
│   ├── telemetry.py             # OpenTelemetry integration
│   ├── distributed.py           # Distributed state backends
│   ├── dependency.py            # Dependency health graph
│   ├── llm.py                   # LLM resilience + provider failover
│   ├── auto.py                  # Auto policy detection
│   ├── policies.py              # Policy dataclass + global policy
│   ├── exceptions.py            # Exception hierarchy
│   ├── metrics.py               # Metrics + percentiles
│   ├── statistics.py            # Summary tables + health
│   ├── profiling.py             # Function profiling
│   ├── reporters.py             # File/Log/Sentry/Slack/Prometheus
│   ├── mock.py                  # Error injection
│   ├── retry_group.py           # All-or-nothing groups
│   ├── utils.py                 # Backoff, jitter, logging
│   └── py.typed                 # PEP 561 marker
├── tests/                        # 190+ tests
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── pytest.ini
└── README.md
```

---

## 🏭 Production Best Practices

1. **Always use jitter** — prevents thundering herd on simultaneous retries.
2. **Set max_delay** — caps exponential backoff to prevent unbounded waits.
3. **Use retry budgets** for high-traffic services — prevents retry storms.
4. **Combine circuit breaker + sliding window** — tolerate sporadic failures.
5. **Add observability** — metrics + reporters + event bus for every critical path.
6. **Use timeouts** for external calls — never let them hang indefinitely.
7. **Graceful degradation** — always provide a fallback for user-facing operations.

---

## 🤝 Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md).

```bash
# Setup
pip install -e ".[dev]"

# Test
pytest tests/ -v

# Format
black src/ tests/ && isort src/ tests/
```

---

## 📋 Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for full release history.

**Latest: v1.1.0** — Resilience Platform release with composable retry primitives, cache with stampede prevention, 5 rate limiting algorithms, 4 bulkhead types, policy composition DSL, adaptive resilience, presets, HTTP intelligence, OpenTelemetry, event bus, distributed state, dependency graph, chaos testing, LLM resilience, auto policy detection, and 190+ tests.

---

## 📄 License

**MIT** © [RaptorVampire](https://github.com/RaptorVampire)