.. _migration:

===================
Migration Guides
===================


From tenacity
=============

tenacity's API maps cleanly to tranq:

.. code-block:: python

   # tenacity
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=60))
   def f(): ...

   # tranq
   from tranq import handle, stop, wait

   @handle(
       on=Exception,
       retry=4,
       wait=wait.exponential(multiplier=1.0, min=1.0, max=60.0),
       stop=stop.after_attempt(5),
   )
   def f(): ...

Or with the composition DSL:

.. code-block:: python

   from tranq import PolicyBuilder, wait, stop

   @PolicyBuilder().retry(
       max_attempts=5,
       wait=wait.exponential(multiplier=1.0, min=1.0, max=60.0),
       stop=stop.after_attempt(5),
   )
   def f(): ...


From backoff
============

.. code-block:: python

   # backoff
   import backoff

   @backoff.on_exception(backoff.expo, ConnectionError, max_tries=5)
   def f(): ...

   # tranq
   from tranq import handle, wait

   @handle(
       on=ConnectionError,
       retry=4,
       wait=wait.exponential(multiplier=1.0, max=60.0),
   )
   def f(): ...


From pyresilience
=================

pyresilience's ``@circuitbreaker``, ``@ratelimiter``, ``@bulkhead`` and
``@cache`` decorators translate directly:

.. code-block:: python

   # pyresilience
   from pyresilience import circuitbreaker, ratelimiter, bulkhead

   @circuitbreaker(failure_threshold=5)
   @ratelimiter(limit=10)
   @bulkhead(max_concurrent=5)
   def f(): ...

   # tranq
   from tranq import PolicyBuilder

   @PolicyBuilder()
       .circuit_breaker(tranq.CircuitBreaker(failure_threshold=5))
       .rate_limit(rate=10)
       .bulkhead(max_concurrent=5)
   def f(): ...
