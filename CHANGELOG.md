# Changelog

All notable changes to **tranq** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-02-17

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
