.. _api-reference:

=============
API Reference
=============

This is the complete reference for every public symbol in **tranq**.

.. toctree::
   :maxdepth: 1
   :caption: Core

   decorators
   primitives
   composition

.. toctree::
   :maxdepth: 1
   :caption: Resilience Primitives

   circuit_breakers
   rate_limiters
   bulkheads
   cache
   fallback

.. toctree::
   :maxdepth: 1
   :caption: Platform

   events
   adaptive
   chaos
   diagnostics
   distributed
   dependency
   presets
   llm
   auto
   telemetry
   metrics

.. toctree::
   :maxdepth: 1
   :caption: Errors

   exceptions


Quick Lookup
============

.. list-table:: Most Used Symbols
   :header-rows: 1
   :widths: 40 60

   * - Symbol
     - Description
   * - :func:`tranq.handle`
     - Sync decorator with full error handling
   * - :func:`tranq.handle_async`
     - Async decorator
   * - :func:`tranq.retry`
     - Sync context manager
   * - :func:`tranq.retry_async`
     - Async context manager
   * - :class:`tranq.PolicyBuilder`
     - Fluent policy composer
   * - :class:`tranq.CircuitBreaker`
     - Count-based circuit breaker
   * - :class:`tranq.SlidingWindowCircuitBreaker`
     - Failure-rate circuit breaker
   * - :func:`tranq.rate_limit`
     - Token-bucket decorator
   * - :func:`tranq.bulkhead`
     - Concurrency limiter decorator
   * - :func:`tranq.cache`
     - Cache-aside decorator
   * - :class:`tranq.EventBus`
     - Pub/sub for resilience events
   * - :func:`tranq.auto`
     - Auto policy detection
