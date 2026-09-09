.. _quickstart:

============
Quick Start
============

This guide walks you through the most common patterns in **tranq** in under
five minutes. Every example is a complete, runnable snippet.


1. The Basic Decorator
======================

The simplest way to add retries to any function:

.. code-block:: python

   import tranq

   @tranq.handle(on=ValueError, retry=3, delay=0.5, backoff=2.0)
   def risky_operation():
       ...

* ``on=ValueError`` — only catch ``ValueError`` (use a tuple for multiple types)
* ``retry=3`` — up to 3 retries (4 total attempts)
* ``delay=0.5`` — base delay of 0.5 seconds
* ``backoff=2.0`` — exponential multiplier

The function will be retried with delays ``0.5, 1.0, 2.0`` seconds.


2. Async Functions
==================

The async variant uses ``asyncio.sleep`` and ``asyncio.wait_for``:

.. code-block:: python

   @tranq.handle_async(on=ConnectionError, retry=2, fallback=lambda: "offline")
   async def fetch_data():
       ...

If all retries fail, the ``fallback`` is returned (and no exception is raised
when ``reraise=False``).


3. Circuit Breaker
==================

Protect downstream services from cascading failures:

.. code-block:: python

   cb = tranq.CircuitBreaker(failure_threshold=5, timeout=60)

   @tranq.handle(on=Exception, circuit_breaker=cb)
   def call_unstable_service():
       ...

After 5 consecutive failures the circuit opens and requests are rejected
immediately with :class:`~tranq.CircuitBreakerError` — no network call is made.


4. Sliding Window Circuit Breaker
=================================

.. versionadded:: 1.1.0

A more sophisticated breaker that opens based on **failure rate**:

.. code-block:: python

   swc = tranq.SlidingWindowCircuitBreaker(
       window_size=100,
       failure_rate_threshold=0.5,   # open if 50% fail
       minimum_calls=10,
   )

   @tranq.handle(on=Exception, circuit_breaker=swc)
   def unreliable_service():
       ...


5. Rate Limiter
===============

.. versionadded:: 1.1.0

Prevent overwhelming downstream APIs:

.. code-block:: python

   @tranq.rate_limit(rate=10, per=1.0, burst=20)
   def api_call():
       ...

Uses a **token bucket** with rate 10 tokens/sec, burst of 20.


6. Bulkhead
===========

.. versionadded:: 1.1.0

Limit concurrency to prevent resource exhaustion:

.. code-block:: python

   @tranq.bulkhead(max_concurrent=5, timeout=10.0)
   def database_query():
       ...

At most 5 concurrent executions. Additional callers wait up to 10 seconds
for a slot, or receive :class:`~tranq.BulkheadFullError`.


7. Policy Composition DSL
=========================

.. versionadded:: 1.1.0

Compose all resilience features into a single decorator:

.. code-block:: python

   from tranq import PolicyBuilder, wait, stop, retry_if

   policy = (
       PolicyBuilder()
       .retry(max_attempts=3, wait=wait.full_jitter(0.5, max=10))
       .timeout(5)
       .circuit_breaker(tranq.SlidingWindowCircuitBreaker(...))
       .rate_limit(rate=10)
       .bulkhead(max_concurrent=5)
       .cache(ttl=60)
       .fallback(lambda: {"status": "cached"})
       .observe(event_bus=bus)
   )

   @policy
   def call_service():
       ...


8. Context Manager
==================

Full feature parity with ``@handle``, but imperative:

.. code-block:: python

   with tranq.retry(on=ValueError, retry=2, delay=0.1) as ctx:
       result = ctx.run(my_function, arg1, kwarg1=value)


9. Async Context Manager
=========================

.. versionadded:: 1.1.0

.. code-block:: python

   async with tranq.retry_async(on=ConnectionError, retry=3) as ctx:
       result = await ctx.run(my_async_function, arg1)


10. Auto Policy Detection
=========================

.. versionadded:: 1.1.0

Let tranq recommend (or apply) the right policy automatically:

.. code-block:: python

   @tranq.auto(verbose=True)   # prints recommendation, does not change behavior
   async def fetch_orders():
       ...

   @tranq.auto(apply=True)     # actually wraps with detected policy
   async def fetch_users():
       ...


What Next?
==========

* Read :doc:`features/index` for in-depth documentation on every feature
* Browse :doc:`examples` for 38 complete runnable scripts
* Consult :doc:`api/index` for the full reference
* Check :doc:`best_practices` for production recommendations
