.. _feature-distributed:

=====================
Distributed Resilience
=====================

.. versionadded:: 1.1.0

Share rate limits, circuit breakers, retry budgets and counters across
processes via a pluggable state backend.


Backends
========

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Backend
     - Description
   * - :class:`~tranq.InMemoryBackend`
     - Single-process default (thread-safe)
   * - :class:`~tranq.RedisBackend`
     - Redis-backed cluster-wide state


Distributed Rate Limiter
========================

Fixed-window rate limiter shared across processes:

.. code-block:: python

   from tranq import RedisBackend, DistributedRateLimiter

   backend = RedisBackend(url="redis://localhost:6379/0")
   limiter = DistributedRateLimiter(
       limit=100,
       window=1.0,
       backend=backend,
       key="tranq:api_calls",
   )

   if limiter.try_acquire():
       call_api()
   else:
       raise RateLimitExceeded("cluster limit exceeded")


Distributed Counter
===================

Shared counter for cluster-wide retry budgets, quotas, etc.:

.. code-block:: python

   from tranq import DistributedCounter

   counter = DistributedCounter(backend=backend, key="tranq:emails_sent")
   counter.incr()
   print(counter.get())


Custom Backends
===============

Implement :class:`~tranq.StateBackend` for PostgreSQL, DynamoDB, etc.:

.. code-block:: python

   from tranq import StateBackend

   class PostgresBackend(StateBackend):
       def incr(self, key, amount=1):
           ...
       def get(self, key, default=0):
           ...
       def set(self, key, value):
           ...
       def expire(self, key, ttl):
           ...


See Also
========

* :doc:`../api/distributed`
* :doc:`rate_limiter` — single-process variants
