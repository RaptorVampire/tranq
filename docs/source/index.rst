.. tranq documentation master file

🌿 tranq — Resilience Platform for Python
==========================================

.. raw:: html

   <p align="center">
     <img src="https://img.shields.io/pypi/v/tranq?style=for-the-badge&color=blue" alt="PyPI">
     <img src="https://img.shields.io/pypi/pyversions/tranq?style=for-the-badge&color=green" alt="Python">
     <img src="https://img.shields.io/badge/license-MIT-orange?style=for-the-badge" alt="MIT">
     <img src="https://img.shields.io/badge/status-Production%2FStable-success?style=for-the-badge" alt="Status">
   </p>

**tranq** is a **production-grade resilience platform** for Python that brings
together the best ideas from ``tenacity``, ``backoff``, ``pyresilience``,
``resilience4j`` and modern microservice patterns — in a single, zero-boilerplate,
decorator-based API.

.. code-block:: python

   import tranq

   @tranq.handle(
       on=ConnectionError,
       retry=4,
       delay=1.0,
       backoff=2.0,
       timeout=5.0,
       circuit_breaker=tranq.SlidingWindowCircuitBreaker(failure_rate_threshold=0.5),
   )
   def call_external_service():
       ...

Why tranq?
----------

Writing repetitive ``try``/``except`` blocks clutters your code and buries
the business logic. Retry loops, circuit breakers, rate limits, timeouts and
cache stampede prevention are **cross-cutting concerns** that should not
pollute your core logic.

**tranq** gives you **declarative error handling** through decorators, context
managers, and a composable policy DSL — so you focus on **what** your code does,
not **how** it recovers from failure.

.. grid:: 1 1 2 3
   :gutter: 3

   .. grid-item-card:: 🔁 Smart Retries
      :link: features/retry
      :link-type: doc

      Exponential, linear, Fibonacci, full/equal/decorrelated jitter,
      composable stop conditions, HTTP intelligence.

   .. grid-item-card:: 🚦 Circuit Breakers
      :link: features/circuit_breaker
      :link-type: doc

      Count-based, sliding-window, slow-call detection, event emission,
      per-service registry.

   .. grid-item-card:: 🚦 Rate Limiting
      :link: features/rate_limiter
      :link-type: doc

      Token bucket, leaky bucket, fixed/sliding window, adaptive,
      distributed (Redis).

   .. grid-item-card:: 🚪 Bulkheads
      :link: features/bulkhead
      :link-type: doc

      Thread, async, queue-based, per-key isolation to prevent cascading
      resource exhaustion.

   .. grid-item-card:: 🗄️ Resilience Cache
      :link: features/cache
      :link-type: doc

      TTL, LRU, single-flight stampede prevention, stale-if-error,
      negative caching.

   .. grid-item-card:: 🧩 Policy Builder
      :link: features/composition
      :link-type: doc

      Fluent DSL combining all features into a single decorator.

   .. grid-item-card:: 🧠 Adaptive Resilience
      :link: features/adaptive
      :link-type: doc

      Automatically tunes timeout, retry and rate limits from observed
      latency and error rate.

   .. grid-item-card:: 🔭 OpenTelemetry Native
      :link: features/telemetry
      :link-type: doc

      Automatic spans, counters and events for every resilience operation.

   .. grid-item-card:: 🤖 LLM Resilience
      :link: features/llm
      :link-type: doc

      Rate limits, Retry-After, provider failover, token budgets.


Design Principles
-----------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Principle
     - Description
   * - 🧘 **Tranquil**
     - Clean, readable, zero-boilerplate. Decorators over try/except.
   * - 🔌 **Non-invasive**
     - No code changes inside your functions required.
   * - 🧩 **Composable**
     - Every feature combines: retry + CB + timeout + cache + metrics + hooks.
   * - 🏭 **Production-ready**
     - Thread-safe, async-safe, contextvar-isolated. 190+ tests.
   * - 📦 **Zero dependencies**
     - Core has no runtime deps. Optional extras for Sentry, Slack, Prometheus, Redis, OpenTelemetry.
   * - 🔍 **Observable**
     - Built-in metrics, profiling, percentiles, health reports, OpenTelemetry.


.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   installation
   quickstart
   design

.. toctree::
   :maxdepth: 2
   :caption: Features
   :hidden:

   features/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   :hidden:

   api/index

.. toctree::
   :maxdepth: 2
   :caption: Guides
   :hidden:

   examples
   testing
   best_practices
   comparison
   migration

.. toctree::
   :maxdepth: 2
   :caption: Project
   :hidden:

   changelog
   contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
