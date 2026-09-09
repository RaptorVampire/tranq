.. _comparison:

===================
Library Comparison
===================

tranq was built to combine the best ideas from existing libraries while
adding features none of them have. This page compares tranq against the
most popular alternatives.


Feature Matrix
==============

.. list-table::
   :header-rows: 1
   :widths: 40 15 15 15 15

   * - Feature
     - **tranq**
     - tenacity
     - backoff
     - pyresilience
   * - Decorator (sync)
     - ✅
     - ✅
     - ✅
     - ✅
   * - Decorator (async)
     - ✅
     - ✅
     - ✅
     - ✅
   * - Circuit Breaker (count)
     - ✅
     - ❌
     - ❌
     - ✅
   * - Circuit Breaker (sliding-window)
     - ✅
     - ❌
     - ❌
     - ❌
   * - Slow-call detection
     - ✅
     - ❌
     - ❌
     - ❌
   * - Rate Limiter (5 algorithms)
     - ✅
     - ❌
     - ❌
     - ✅
   * - Bulkhead (4 types)
     - ✅
     - ❌
     - ❌
     - ✅
   * - Retry Budget
     - ✅
     - ❌
     - ❌
     - ✅
   * - Hedged Requests
     - ✅
     - ❌
     - ❌
     - ❌
   * - Timeout (sync + async)
     - ✅
     - ⚠️
     - ❌
     - ✅
   * - Deadline propagation
     - ✅
     - ❌
     - ❌
     - ❌
   * - Event Hooks
     - ✅
     - ⚠️
     - ⚠️
     - ❌
   * - Unified Event Bus
     - ✅
     - ❌
     - ❌
     - ❌
   * - Context Manager
     - ✅
     - ❌
     - ❌
     - ❌
   * - Async Context Manager
     - ✅
     - ❌
     - ❌
     - ❌
   * - Retry Groups
     - ✅
     - ❌
     - ❌
     - ❌
   * - Metrics + Percentiles
     - ✅
     - ❌
     - ❌
     - ✅
   * - Statistics / Health Reports
     - ✅
     - ❌
     - ❌
     - ❌
   * - Reporters (5 built-in)
     - ✅
     - ❌
     - ❌
     - ❌
   * - Mock Errors + Chaos
     - ✅
     - ❌
     - ❌
     - ❌
   * - Dependency Injection
     - ✅
     - ❌
     - ❌
     - ❌
   * - Global Policy
     - ✅
     - ❌
     - ❌
     - ❌
   * - Stateful Retry
     - ✅
     - ❌
     - ❌
     - ❌
   * - Cache + Stampede Prevention
     - ✅
     - ❌
     - ❌
     - ✅
   * - Policy Composition DSL
     - ✅
     - ❌
     - ❌
     - ❌
   * - Adaptive Resilience
     - ✅
     - ❌
     - ❌
     - ❌
   * - Policy Presets
     - ✅
     - ❌
     - ❌
     - ✅
   * - HTTP Intelligence
     - ✅
     - ❌
     - ❌
     - ✅
   * - OpenTelemetry Native
     - ✅
     - ❌
     - ❌
     - ❌
   * - Distributed State
     - ✅
     - ❌
     - ❌
     - ❌
   * - Dependency Graph
     - ✅
     - ❌
     - ❌
     - ❌
   * - LLM Resilience
     - ✅
     - ❌
     - ❌
     - ✅
   * - Auto Policy Detection
     - ✅
     - ❌
     - ❌
     - ❌
   * - Zero Dependencies
     - ✅
     - ✅
     - ✅
     - ❌


When to Choose tranq
====================

Choose tranq when you want:

* A single library that covers **every** resilience pattern
* A composable **policy builder** instead of massive decorator args
* Built-in **observability** (metrics, percentiles, OpenTelemetry, events)
* **Distributed state** for cluster-wide rate limits and budgets
* **LLM-aware** resilience with provider failover
* **Adaptive** tuning based on observed signals
* **Zero dependencies** by default, opt-in extras for integrations


When to Choose Alternatives
===========================

* **tenacity** — if you only need basic retry/backoff and want the most
  battle-tested option
* **backoff** — if you want a minimal decorator-only library
* **pyresilience** — if you are already in a pyresilience-based stack
