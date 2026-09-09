.. _feature-rate-limiter:

==============
Rate Limiting
==============

tranq provides five rate-limiting algorithms and an adaptive variant. All are
thread-safe and usable as decorators or standalone primitives.


Token Bucket (default)
======================

Allows **bursts** up to the bucket capacity while enforcing a sustained rate.

.. code-block:: python

   from tranq import rate_limit

   @rate_limit(rate=10, per=1.0, burst=20)
   def api_call():
       """10 calls/sec sustained, burst up to 20."""
       ...


Leaky Bucket
============

Requests drain at a fixed rate; incoming requests fill the bucket.

.. code-block:: python

   from tranq import LeakyBucket

   lb = LeakyBucket(capacity=20, leak_rate=5.0)  # 5 req/sec
   if lb.try_acquire():
       do_work()


Fixed Window
============

Simple counter per fixed time window. Fast and predictable.

.. code-block:: python

   from tranq import FixedWindowLimiter

   fw = FixedWindowLimiter(limit=100, window=60.0)  # 100 per minute
   if fw.try_acquire():
       do_work()


Sliding Window
==============

More precise than fixed window; tracks individual request timestamps.

.. code-block:: python

   from tranq import SlidingWindowLimiter

   sw = SlidingWindowLimiter(limit=100, window=60.0)


Adaptive Rate Limiter
=====================

.. versionadded:: 1.1.0

Automatically reduces rate on failures and recovers on success:

.. code-block:: python

   from tranq import AdaptiveRateLimiter

   arl = AdaptiveRateLimiter(
       base_rate=100.0,
       decrease_factor=0.5,    # halve on failure
       increase_factor=1.1,    # grow slowly on success
       min_rate=1.0,
   )

   try:
       result = call_service()
       arl.record_success()
   except Exception:
       arl.record_failure()
       raise


Blocking vs Non-Blocking
========================

All limiters support both modes:

.. code-block:: python

   # Non-blocking: return False immediately
   if not rl.try_acquire():
       return None

   # Blocking with timeout: wait up to 5 seconds
   if not rl.acquire(timeout=5.0):
       raise RateLimitExceeded("...")

   # Wait forever
   rl.acquire(timeout=None)


Decorator Form
==============

.. code-block:: python

   @rate_limit(rate=10, per=1.0, timeout=5.0, raise_on_limit=True)
   def call():
       ...

The decorator auto-detects sync vs async and uses the appropriate acquire
method.


See Also
========

* :doc:`../api/rate_limiters`
* :doc:`distributed` — cluster-wide rate limiting via Redis
