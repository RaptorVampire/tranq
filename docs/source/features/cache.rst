.. _feature-cache:

==================
Resilience Cache
==================

tranq includes an in-memory cache designed specifically for resilience:
TTL, LRU eviction, **stampede prevention**, stale-if-error, and negative
caching.


Basic Usage
===========

.. code-block:: python

   from tranq import cache

   @cache(ttl=60, maxsize=1024)
   def expensive(x):
       ...

First call computes and caches; subsequent calls within 60 seconds return
the cached value.


Stampede Prevention
===================

When many concurrent callers miss the cache simultaneously, only **one**
computes the value (single-flight). Others wait and share the result.

.. code-block:: python

   from tranq import TranqCache

   store = TranqCache(ttl=60, maxsize=256)

   def loader():
       return expensive_computation()

   result = store.single_flight("key", loader)


The async variant uses :func:`asyncio.ensure_future`:

.. code-block:: python

   astore = AsyncTranqCache(ttl=60)
   result = await astore.single_flight_async("key", async_loader)


Stale-If-Error
==============

Serve expired values when the loader fails:

.. code-block:: python

   store = TranqCache(ttl=5.0, stale_if_error=True)
   store.set("key", "fresh_value")

   # Later: TTL has expired, loader raises
   hit, stale = store.get_stale("key")
   # stale = "fresh_value"


This pattern is essential for graceful degradation: prefer a 5-minute-old
value over a hard error.


Negative Caching
================

Cache failures as negative results to prevent repeated attempts:

.. code-block:: python

   store.set("missing_key", None, negative=True, ttl=60.0)

   hit, value = store.get("missing_key")
   # hit=True, value=None

Configure ``negative_ttl`` separately from the positive TTL:

.. code-block:: python

   store = TranqCache(ttl=300.0, negative_ttl=30.0)


LRU Eviction
============

When ``maxsize`` is reached, the least-recently-used entry is evicted:

.. code-block:: python

   store = TranqCache(ttl=None, maxsize=2)
   store.set("a", 1)
   store.set("b", 2)
   store.set("c", 3)  # "a" is evicted


Metrics
=======

Every cache tracks its own statistics:

.. code-block:: python

   print(store.metrics())
   # {
   #   "hits": 150,
   #   "misses": 20,
   #   "stale_hits": 3,
   #   "negative_hits": 5,
   #   "sets": 40,
   #   "evictions": 2,
   # }


See Also
========

* :doc:`../api/cache` — full API reference
