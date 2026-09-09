.. _feature-fallback:

=========
Fallbacks
=========

Fallbacks provide graceful degradation when all retries are exhausted.
tranq supports static values, callables, async callables, chains, cached
values, and exception-aware conditional fallbacks.


Static Fallback
===============

.. code-block:: python

   @tranq.handle(on=Exception, retry=2, fallback=lambda: "cached", reraise=False)
   def get_live_data():
       ...


Callable Fallback
=================

Receives the original arguments:

.. code-block:: python

   def compute_fallback(user_id, include_history=False):
       return {"user_id": user_id, "source": "cache", "stale": True}

   @tranq.handle(on=Exception, retry=1, fallback=compute_fallback, reraise=False)
   def get_user(user_id, include_history=False):
       ...


Fallback Chain
==============

.. versionadded:: 1.1.0

Try multiple fallbacks in sequence:

.. code-block:: python

   from tranq import FallbackChain

   chain = FallbackChain(
       primary_source,
       redis_cache,
       lambda: static_default,
   )

   # Runs each in order; returns the first that succeeds
   result = chain.run(*args, **kwargs)


Cached Fallback (Stale-While-Failing)
=====================================

.. versionadded:: 1.1.0

Serve the last successful result:

.. code-block:: python

   from tranq import CachedFallback

   cached = CachedFallback(default=None)

   # Remember successful results
   cached.remember(last_good_value)

   # Serve from cache on failure
   @tranq.handle(on=Exception, fallback=cached, reraise=False)
   def get_data():
       ...


Conditional Fallback
====================

.. versionadded:: 1.1.0

Choose a fallback based on the exception type:

.. code-block:: python

   from tranq import ConditionalFallback

   cf = (ConditionalFallback()
         .when(TimeoutError, lambda: "slow_response")
         .when(ConnectionError, lambda: "offline")
         .when(Exception, lambda: "error"))


See Also
========

* :doc:`../api/fallback`
* :doc:`cache` — stale-if-error pattern
