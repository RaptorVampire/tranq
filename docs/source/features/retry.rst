.. _feature-retry:

=============
Smart Retries
=============

Retries are the foundation of resilient systems. tranq provides a rich set of
**wait strategies**, **stop conditions** and **retry predicates** — all
composable and all Tenacity-compatible in spirit.


Wait Strategies
===============

A wait strategy is a callable ``wait(attempt) -> seconds``. All built-in
strategies are classes in :mod:`tranq.wait` and also exposed via the
:attr:`tranq.wait` namespace.

.. code-block:: python

   from tranq import wait

   # Constant delay
   w = wait.fixed(1.0)

   # Exponential with multiplier and cap
   w = wait.exponential(multiplier=0.5, max=30.0)

   # Fibonacci
   w = wait.fibonacci(multiplier=1.0)

   # Full jitter (uniform in [0, exponential])
   w = wait.full_jitter(multiplier=1.0, max=10.0)

   # Equal jitter (half fixed + half random)
   w = wait.equal_jitter(multiplier=1.0, max=30.0)

   # Decorrelated (AWS style)
   w = wait.decorrelate_jitter(base=1.0, cap=60.0)

   # Compose strategies
   w = wait.fixed(0.5) + wait.exponential(multiplier=1.0, max=10.0)


Strategies support ``min`` and ``max`` clamping:

.. code-block:: python

   w = wait.exponential(multiplier=0.1, min=1.0, max=60.0)

   # attempt 0 -> 1.0  (clamped up from 0.1)
   # attempt 10 -> 60.0 (clamped down)


Stop Conditions
===============

A stop condition is a callable ``stop(attempt, elapsed) -> bool``. Built-ins
live in :mod:`tranq.stop`:

.. code-block:: python

   from tranq import stop

   # Stop after N attempts
   s = stop.after_attempt(5)

   # Stop after T seconds total
   s = stop.after_delay(60.0)

   # Stop if next attempt would exceed deadline
   s = stop.before_deadline(deadline=120.0, expected_next=5.0)

   # Custom predicate
   s = stop.when(lambda attempt, elapsed: attempt > 10 or elapsed > 60)


**Compose conditions** with ``&`` (AND) and ``|`` (OR):

.. code-block:: python

   # Stop after 5 attempts OR 30 seconds (whichever first)
   s = stop.after_attempt(5) | stop.after_delay(30.0)

   # Stop after 5 attempts AND 30 seconds (both must be true)
   s = stop.after_attempt(5) & stop.after_delay(30.0)


Retry Predicates
================

A retry predicate is a callable ``predicate(exception) -> bool``. It decides
whether a failure should trigger a retry.

.. code-block:: python

   from tranq import retry_if

   # Retry specific exception types
   p = retry_if.exception_type((ConnectionError, TimeoutError))

   # Retry specific HTTP status codes
   p = retry_if.http_status((429, 500, 502, 503, 504))

   # Retry on Retry-After header
   p = retry_if.retry_after()

   # Retry anywhere in the exception chain
   p = retry_if.exception_chain(ConnectionError)

   # Custom predicate
   p = retry_if.exception(lambda e: "transient" in str(e))


**Compose predicates**:

.. code-block:: python

   should_retry = (
       retry_if.http_status((429, 503)) |
       retry_if.exception_type(ConnectionError)
   )

   @tranq.handle(on=Exception, retry=3, retry_if=should_retry)
   def call_api():
       ...


Full Example
============

.. code-block:: python

   import tranq
   from tranq import wait, stop, retry_if

   policy = (
       tranq.PolicyBuilder()
       .retry(
           max_attempts=10,
           wait=wait.full_jitter(0.5, max=30.0),
           stop=stop.after_attempt(10) | stop.after_delay(300),
           retry_if=retry_if.http_status((429, 503)) | retry_if.retry_after(),
       )
       .timeout(10.0)
   )

   @policy
   def call_external_api():
       ...


See Also
========

* :doc:`../api/primitives` — full API reference for wait/stop/retry_if
* :doc:`composition` — the policy builder DSL
* :doc:`presets` — ready-made configs for common backends
