.. _feature-bulkhead:

=========
Bulkheads
=========

Bulkheads isolate concurrent executions to prevent resource exhaustion — just
like the watertight compartments of a ship. tranq provides four types.


Thread-Based Bulkhead
=====================

A simple semaphore limiting concurrent sync executions:

.. code-block:: python

   from tranq import bulkhead

   @bulkhead(max_concurrent=5, timeout=10.0)
   def database_query():
       ...


Async Bulkhead
==============

For async code, using :class:`asyncio.Semaphore`:

.. code-block:: python

   @bulkhead(max_concurrent=20, timeout=5.0)
   async def http_request():
       ...


Queue-Based Bulkhead
====================

.. versionadded:: 1.1.0

Bounded queue plus fixed worker pool:

.. code-block:: python

   from tranq import QueueBulkhead

   qb = QueueBulkhead(max_concurrent=5, queue_size=10)
   result = qb.submit(my_func, arg1, arg2)  # raises BulkheadFullError if full


Per-Key Isolation
=================

.. versionadded:: 1.1.0

One independent bulkhead per key (e.g. per host, per user):

.. code-block:: python

   from tranq import KeyedBulkhead

   kb = KeyedBulkhead(max_concurrent=5, timeout=2.0)
   if kb.acquire("host-A"):
       try:
           call_host_a()
       finally:
           kb.release("host-A")


Introspection
=============

Every bulkhead exposes its current state:

.. code-block:: python

   @bulkhead(max_concurrent=3)
   def work():
       ...

   print(work.bulkhead.active)          # current concurrent count
   print(work.bulkhead.max_concurrent)  # configured limit


See Also
========

* :doc:`../api/bulkheads`
