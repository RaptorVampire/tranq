.. _feature-composition:

=====================
Policy Composition
=====================

.. versionadded:: 1.1.0

The heart of the platform: a fluent DSL that composes every resilience
feature into a single decorator.


Basic Usage
===========

.. code-block:: python

   from tranq import PolicyBuilder, wait, stop, retry_if

   policy = (
       PolicyBuilder()
       .retry(max_attempts=3, wait=wait.full_jitter(0.5, max=10))
       .timeout(5)
   )

   @policy
   def call_service():
       ...


Full Example
============

.. code-block:: python

   from tranq import (
       PolicyBuilder, wait, stop, retry_if,
       SlidingWindowCircuitBreaker, EventBus, events,
   )

   bus = EventBus()
   bus.subscribe(events.CircuitOpened, lambda e: alert(e))

   policy = (
       PolicyBuilder()
       .retry(
           max_attempts=5,
           wait=wait.full_jitter(0.5, max=30),
           stop=stop.after_attempt(5) | stop.after_delay(120),
           retry_if=retry_if.http_status((429, 503)) | retry_if.retry_after(),
       )
       .timeout(10)
       .circuit_breaker(
           SlidingWindowCircuitBreaker(failure_rate_threshold=0.5)
       )
       .rate_limit(rate=100, per=1.0, burst=200)
       .bulkhead(max_concurrent=10)
       .cache(ttl=60, maxsize=1024)
       .fallback(FallbackChain(cached_fallback, lambda: "default"))
       .observe(event_bus=bus, telemetry=True, service="payment")
   )

   @policy
   def call_payment_api():
       ...


Execution Order
===============

The composed policy wraps your function in this order (outermost first):

1. **Cache lookup** — return cached value on hit
2. **Rate limiter** — reject or wait
3. **Bulkhead** — acquire slot or reject
4. **Circuit breaker** — allow or reject
5. **Retry loop** with timeout + wait + stop + retry_if
6. **On success**: cache store + event emission
7. **On failure**: stale-if-error → fallback chain → raise
8. **Bulkhead release**


Shortcut Decorator
==================

For simple cases, :func:`~tranq.resilient` builds a policy inline:

.. code-block:: python

   from tranq import resilient

   @resilient(max_attempts=3, timeout=5, fallback=lambda: "fb", cache_ttl=60)
   def f():
       ...


See Also
========

* :doc:`../api/composition`
* :doc:`retry` — composable wait/stop/retry_if
