.. _features:

========
Features
========

tranq provides a complete resilience toolkit organized into composable
building blocks.

.. toctree::
   :maxdepth: 1

   retry
   circuit_breaker
   rate_limiter
   bulkhead
   timeout
   cache
   fallback
   events
   adaptive
   presets
   chaos
   diagnostics
   composition
   llm
   distributed
   telemetry
   dependency


Feature Matrix
==============

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Feature
     - Description
   * - 🔁 **Smart retries**
     - Exponential, linear, fibonacci, custom callable. Full/equal/decorrelated jitter. Composable with ``+``.
   * - 🛑 **Stop conditions**
     - after_attempt, after_delay, before_deadline, custom predicate. Composable with ``&``/``|``.
   * - 🧪 **Retry predicates**
     - exception_type, http_status, exception_chain, retry_after, result. Composable.
   * - ⏱️ **Timeouts**
     - Per-attempt, total-operation, deadline propagation. Sync & async.
   * - 🚦 **Circuit Breakers**
     - Count-based, sliding-window, slow-call, events, registry.
   * - 🚦 **Rate Limiting**
     - Token bucket, leaky bucket, fixed/sliding window, adaptive, distributed.
   * - 🚪 **Bulkheads**
     - Thread, async, queue-based, per-key.
   * - 🗄️ **Cache**
     - TTL, LRU, stampede prevention, stale-if-error, negative caching, metrics.
   * - 🔄 **Fallback**
     - Static, callable, async, chain, cached, conditional.
   * - 📡 **Event Bus**
     - 14 lifecycle event types, pub/sub.
   * - 🧠 **Adaptive Resilience**
     - Auto-tune timeout/retry/rate from observed signals.
   * - 🎯 **Presets**
     - http, database, redis, kafka, grpc, llm.
   * - 🌐 **HTTP Intelligence**
     - Retryable status detection, Retry-After parsing.
   * - 🩺 **Diagnostics**
     - Per-service health, recommendations.
   * - 🧪 **Chaos Testing**
     - Latency, error, timeout injection.
   * - 🔭 **OpenTelemetry**
     - Spans, counters, events (optional).
   * - 🧬 **Distributed**
     - Redis-backed rate limits, budgets, counters.
   * - 🕸️ **Dependency Graph**
     - Track health of named dependencies.
   * - 🤖 **LLM Resilience**
     - Provider failover, token budgets, Retry-After.
   * - 🏆 **Auto Policy**
     - Detect operation type and recommend policy.
   * - 🧩 **Policy Builder**
     - Fluent DSL composing all features.
