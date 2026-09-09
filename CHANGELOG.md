# Changelog

All notable changes to **tranq** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-09-09

### Added — Resilience Platform Features

#### Retry Primitives (Tenacity Parity)
- **Composable wait strategies**: `wait.fixed`, `wait.none`, `wait.random`,
  `wait.exponential`, `wait.fibonacci`, `wait.incrementing` (linear),
  `wait.random_exponential` (full jitter), `wait.equal_jitter`,
  `wait.decorrelate_jitter`, `wait.combine`. All support `min`/`max` clamping
  and composition via `+`.
- **Composable stop conditions**: `stop.after_attempt`, `stop.after_delay`,
  `stop.before_deadline`, `stop.never`, `stop.when(predicate)`. Composable
  with `&` (AND) and `|` (OR).
- **Retry predicates**: `retry_if.exception_type`, `retry_if.not_exception_type`,
  `retry_if.exception(predicate)`, `retry_if.result(predicate)`,
  `retry_if.http_status`, `retry_if.exception_chain`, `retry_if.retry_after`.
  Composable with `&` / `|`.

#### Cache
- `TranqCache` / `AsyncTranqCache`: TTL, LRU eviction, maxsize, per-key locking,
  **stampede prevention** (single-flight), stale-if-error, negative caching,
  cache metrics (`hits`, `misses`, `stale_hits`, `evictions`).
- `@cache(ttl=..., maxsize=...)` decorator for cache-aside semantics (sync & async).

#### Enhanced Rate Limiting
- `LeakyBucket`: leaky bucket algorithm.
- `FixedWindowLimiter`: fixed window counter.
- `SlidingWindowLimiter`: sliding window log (precise).
- `AdaptiveRateLimiter`: auto-adjusts rate based on success/failure signals.

#### Enhanced Bulkhead
- `QueueBulkhead`: bounded queue + worker pool isolation.
- `KeyedBulkhead`: per-key isolation (e.g., per-host concurrency limits).

#### Enhanced Circuit Breaker
- Slow-call detection (`slow_call_duration`, `slow_call_rate_threshold`).
- State-change events emitted to `EventBus`.
- `BreakerRegistry`: shared named breakers for per-service isolation.

#### Advanced Hedging
- `hedged_quorum()`: return once N of M attempts succeed.
- `PercentileHedgeDelay`: adaptive hedge delay based on latency percentiles.

#### Fallback
- `FallbackChain`: try multiple fallbacks in sequence.
- `CachedFallback`: serve last successful result (stale-while-failing).
- `ConditionalFallback`: choose fallback based on exception type.

#### Policy Composition DSL
- `PolicyBuilder`: fluent API to compose retry + timeout + circuit breaker +
  rate limit + bulkhead + cache + fallback + event bus into a single decorator.
- `ResiliencePolicy`: the composed policy object (sync & async).
- `@resilient(...)`: shortcut decorator builder.

#### Event Bus
- `EventBus` with publish/subscribe for 14 resilience event types:
  `RetryStarted`, `RetryCompleted`, `CircuitOpened`, `CircuitClosed`,
  `CircuitHalfOpened`, `TimeoutTriggered`, `RateLimitExceeded`,
  `BulkheadRejected`, `FallbackTriggered`, `CacheHit`, `CacheMiss`,
  `HedgeStarted`, `OperationSucceeded`, `OperationFailed`.
- Wildcard (`"*"`) subscriptions supported.

#### Adaptive Resilience
- `AdaptiveController`: observes latency, error rate, traffic and recommends
  adjusted timeout/retry/rate-limit parameters automatically.

#### Policy Presets
- Ready-made configs: `presets.http()`, `presets.database()`, `presets.redis()`,
  `presets.kafka()`, `presets.queue()`, `presets.grpc()`, `presets.llm()`.

#### HTTP Intelligence
- `is_retryable()`, `is_retryable_status()`: detect retryable HTTP status codes.
- `parse_retry_after()`: parse `Retry-After` / `X-RateLimit-Reset` headers.
- `recommended_wait()`: compute wait time honoring Retry-After.

#### Diagnostics
- `diagnostics()`: per-service health, circuit states, recommended actions.
- `render_diagnostics()`: human-readable resilience report.

#### Chaos Testing Framework
- `chaos(latency=..., error_rate=..., timeout_rate=...)` context manager.
- `ChaosInjector`: inject latency, errors, timeouts at operation boundaries.
- `chaos_wrapped()`: decorator applying chaos injection.
- `chaos_report()` / `reset_chaos_reports()`: session reports.

#### OpenTelemetry Integration
- `Telemetry` class: emits spans and counters (graceful no-op when not installed).
- `@telemetry(service=...)` decorator for automatic span creation.

#### Distributed Resilience
- `StateBackend` interface with `InMemoryBackend` and `RedisBackend`.
- `DistributedRateLimiter`: cluster-wide fixed-window rate limiting.
- `DistributedCounter`: shared counter for cluster-wide budgets.

#### Dependency-Aware Resilience
- `DependencyGraph`: track health of named dependencies, aggregate service
  health, identify failing dependencies.

#### LLM Resilience
- `@llm(max_attempts=..., providers=[...])`: rate-limit handling, Retry-After,
  automatic provider failover via `FallbackChain`.

#### Auto Policy Detection
- `@auto(apply=False, verbose=True)`: detect operation type from function name,
  recommend a preset policy. Safe by default (recommend-only mode).
- `recommend_policy(func)`: inspect and return recommended config dict.

#### Timeout Utilities
- `Deadline`: absolute deadline with `remaining()` / `expired()`.
- `DeadlineExceededError`: raised when overall deadline passes.

### Changed
- Version bumped to `1.1.0`.
- `__init__.py` now exports **101 symbols** covering all platform features.
- New exceptions added to `exceptions.py` (no existing exceptions removed).

### Fixed
- Name-shadowing bug in `presets.py`: `from . import wait as _wait` resolved to
  the namespace class instead of the module due to `__init__.py` rebinding.
  Fixed by using direct class imports (`from .wait import wait_exponential`).
- Fibonacci test expectation corrected to match established `compute_backoff`
  behavior (attempt 4 → multiplier 5, consistent with existing tests).

## [1.0.0] - 2026-09-08

### Added
- **Timeout support** (`timeout=`) for both `@handle` and `@handle_async`
  (thread-based for sync, `asyncio.wait_for` for async). Raises `FunctionTimeoutError`.
- **Lifecycle event hooks**: `on_retry`, `on_success`, `on_failure`, `on_complete`
  (sync & async, may be coroutines in async mode).
- **Rate limiting**: `RateLimiter` (token bucket) + `@rate_limit` decorator.
- **Bulkhead isolation**: `Bulkhead` / `AsyncBulkhead` + `@bulkhead` decorator.
- **Retry budget**: `RetryBudget` to prevent retry storms.
- **Hedged requests**: `hedged_call()` and `@hedged` for async.
- **Sliding-window circuit breaker**: `SlidingWindowCircuitBreaker` and
  `AsyncSlidingWindowCircuitBreaker` (failure-rate based).
- **Async context manager**: `tranq.retry_async(...)` usable with `async with`.
- **Advanced metrics**: `p50`, `p95`, `p99`, `min`, `max`, `avg`, `error_rate`.
- **Statistics**: `summary_table()`, `overall_health()`, `render_report()`.
- **Real reporters**: `LogReporter`, `PrometheusReporter`, and working
  `SentryReporter` / `SlackReporter` (optional dependencies, lazy imports).
- New exceptions: `FunctionTimeoutError`, `RateLimitExceeded`,
  `BulkheadFullError`, `RetryBudgetExhaustedError`.
- `py.typed` marker + full type hints (PEP 561).
- GitHub Actions CI (Python 3.9–3.13 on Linux/Windows/macOS) and auto-publish.

### Changed
- `CircuitBreaker` / `AsyncCircuitBreaker` gained `reset()` and `failure_count`.
- Decorators detect async circuit breakers via duck-typing
  (`iscoroutinefunction(cb.allow_request)`), so any async breaker works.
- `FileReporter` writes strict JSON lines.

### Fixed
- **Success-path bug**: the retry loop no longer re-invokes a function that has
  already returned an accepted result.
- **Python 3.9 compatibility**: replaced PEP 585 `tuple[...]` generics with
  `typing.Tuple[...]`.
- `AsyncBulkhead.acquire()` with `timeout=0` now behaves like the sync version
  (non-blocking) instead of always failing.
- `hedged_call()` now launches replacement attempts after a failure instead of
  stopping when the in-flight set becomes empty.

## [0.3.0] - Previous

### Added
- Decorators `@handle` / `@handle_async`, retry/backoff strategies, circuit
  breakers, context manager, retry groups, metrics, profiling, reporters,
  mock error injection, dependency injection, global policy, stateful retry.