.. tranq documentation master file

🌿 tranq
========

**Calm, production-grade error handling & resilience for Python.**

.. image:: https://img.shields.io/badge/PyPI-tranq-blue?style=flat-square
   :target: https://pypi.org/project/tranq/
.. image:: https://img.shields.io/badge/python-3.9%2B-green?style=flat-square
.. image:: https://img.shields.io/badge/tests-135%2B%20passing-brightgreen?style=flat-square
.. image:: https://img.shields.io/badge/license-MIT-orange?style=flat-square

Installation
------------

.. code-block:: bash

   pip install tranq
   pip install tranq[all]      # optional integrations

Quick Start
-----------

.. code-block:: python

   import tranq

   @tranq.handle(on=ConnectionError, retry=3, delay=0.5, timeout=5.0)
   def fetch():
       ...

   @tranq.handle_async(on=TimeoutError, retry=2, fallback=lambda: "offline")
   async def fetch_async():
       ...

Resilience Features (v1.0.0)
----------------------------

* **Retry + backoff** (exponential / linear / fibonacci / custom, jitter, max_delay)
* **Timeouts** via ``timeout=`` (raises ``FunctionTimeoutError``)
* **Event hooks**: ``on_retry``, ``on_success``, ``on_failure``, ``on_complete``
* **Circuit breakers**: count-based and sliding-window (failure-rate), sync & async
* **Rate limiter**: ``@tranq.rate_limit`` (token bucket)
* **Bulkhead**: ``@tranq.bulkhead`` (concurrency isolation)
* **Retry budget**: ``tranq.RetryBudget``
* **Hedged requests**: ``tranq.hedged`` / ``tranq.hedged_call``
* **Context managers**: ``tranq.retry`` and ``async with tranq.retry_async``
* **Retry groups**: ``tranq.retry_group`` / ``tranq.async_retry_group``
* **Metrics**: counts, error-rate and p50/p95/p99 latencies
* **Statistics**: ``summary_table``, ``overall_health``, ``render_report``
* **Reporters**: File, Log, Sentry, Slack, Prometheus
* **Mock errors**, **dependency injection**, **global policy**, **stateful retry**

Example: sliding-window circuit breaker
---------------------------------------

.. code-block:: python

   swc = tranq.SlidingWindowCircuitBreaker(
       window_size=100, failure_rate_threshold=0.5, minimum_calls=10)

   @tranq.handle(on=Exception, circuit_breaker=swc)
   def call_service():
       ...

Example: async context manager
------------------------------

.. code-block:: python

   async with tranq.retry_async(on=ConnectionError, retry=3) as ctx:
       result = await ctx.run(my_async_func, arg)

API Reference
-------------

Decorators
~~~~~~~~~~

.. py:function:: tranq.handle(...)
.. py:function:: tranq.handle_async(...)
.. py:function:: tranq.rate_limit(rate, per=1.0, burst=None, timeout=None, raise_on_limit=True)
.. py:function:: tranq.bulkhead(max_concurrent, timeout=None, raise_on_full=True)
.. py:function:: tranq.hedged(hedge_delay=0.1, max_hedges=2)
.. py:function:: tranq.profile(func)
.. py:function:: tranq.async_profile(func)

Context managers
~~~~~~~~~~~~~~~~

.. py:function:: tranq.retry(...)
.. py:function:: tranq.retry_async(...)

Circuit breakers
~~~~~~~~~~~~~~~~

.. py:class:: tranq.CircuitBreaker(failure_threshold=5, timeout=60.0, half_open_requests=1)
.. py:class:: tranq.AsyncCircuitBreaker(...)
.. py:class:: tranq.SlidingWindowCircuitBreaker(window_size=100, failure_rate_threshold=0.5, timeout=60.0, half_open_requests=1, minimum_calls=10)
.. py:class:: tranq.AsyncSlidingWindowCircuitBreaker(...)

Resilience primitives
~~~~~~~~~~~~~~~~~~~~~

.. py:class:: tranq.RateLimiter(rate, per=1.0, burst=None)
.. py:class:: tranq.Bulkhead(max_concurrent, timeout=None)
.. py:class:: tranq.AsyncBulkhead(max_concurrent, timeout=None)
.. py:class:: tranq.RetryBudget(ttl=60.0, ratio=0.2, min_tokens=10)
.. py:function:: tranq.hedged_call(func, args=(), kwargs=None, hedge_delay=0.1, max_hedges=2)

Metrics & statistics
~~~~~~~~~~~~~~~~~~~~

.. py:function:: tranq.get_metrics(include_durations=False)
.. py:function:: tranq.reset_metrics()
.. py:function:: tranq.summary_table(metrics=None)
.. py:function:: tranq.overall_health(metrics=None)
.. py:function:: tranq.render_report(metrics=None)
.. py:function:: tranq.get_profile(name=None)

Policies
~~~~~~~~

.. py:class:: tranq.Policy
.. py:function:: tranq.set_global_policy(policy)
.. py:function:: tranq.get_global_policy()

Exceptions
~~~~~~~~~~

.. py:exception:: tranq.TranqError
.. py:exception:: tranq.RetryExhaustedError
.. py:exception:: tranq.CircuitBreakerError
.. py:exception:: tranq.ResultNotAcceptedError
.. py:exception:: tranq.RetryGroupError
.. py:exception:: tranq.FunctionTimeoutError
.. py:exception:: tranq.RateLimitExceeded
.. py:exception:: tranq.BulkheadFullError
.. py:exception:: tranq.RetryBudgetExhaustedError

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   self

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
