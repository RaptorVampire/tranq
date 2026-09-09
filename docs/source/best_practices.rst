.. _best-practices:

===================
Production Best Practices
===================

Follow these rules to get the most out of tranq in production.


1. Always Use Jitter
====================

Without jitter, many clients that failed simultaneously will retry at
exactly the same time (**thundering herd**). Always add jitter.

.. code-block:: python

   # Good
   @tranq.handle(on=Exception, retry=3, delay=1.0, backoff=2.0, jitter=True)

   # Bad — thundering herd risk
   @tranq.handle(on=Exception, retry=3, delay=1.0, backoff=2.0, jitter=False)

Better yet, use :func:`~tranq.wait.full_jitter` which has jitter built in.


2. Always Set max_delay
========================

Without a cap, exponential backoff can grow unbounded:

.. code-block:: python

   # Good — capped at 60 seconds
   @tranq.handle(on=Exception, retry=10, delay=1.0, backoff=2.0, max_delay=60.0)

   # Bad — attempt 30 waits 1073741824 seconds
   @tranq.handle(on=Exception, retry=30, delay=1.0, backoff=2.0)


3. Use Retry Budgets for High-Traffic Services
==============================================

Without a budget, a failing downstream can cause an avalanche of retries
that makes the situation worse.

.. code-block:: python

   budget = tranq.RetryBudget(ttl=60, ratio=0.1, min_tokens=5)

   @tranq.handle(on=Exception, retry=5, retry_budget=budget)
   def high_traffic_handler():
       ...


4. Combine Circuit Breaker + Sliding Window
===========================================

For services with intermittent failures, prefer failure-rate over
consecutive count:

.. code-block:: python

   cb = tranq.SlidingWindowCircuitBreaker(
       window_size=200,
       failure_rate_threshold=0.3,  # 30% failure rate triggers
       minimum_calls=20,            # Need 20 samples first
       timeout=30.0,
   )


5. Add Observability
====================

Every critical path should emit metrics, events, and spans:

.. code-block:: python

   @tranq.handle(
       on=Exception,
       retry=3,
       metrics=True,
       metric_prefix="checkout.payment",
       reporters=[
           tranq.LogReporter(),
           tranq.SentryReporter(dsn=SENTRY_DSN),
       ],
   )
   @tranq.telemetry(service="payment")
   def process_payment():
       ...


6. Always Use Timeouts for External Calls
==========================================

Never let external calls hang indefinitely:

.. code-block:: python

   @tranq.handle(on=Exception, retry=2, timeout=5.0)
   def call_third_party():
       ...


7. Provide Fallbacks for User-Facing Operations
=================================================

Serve cached or default data instead of hard errors:

.. code-block:: python

   @tranq.handle(
       on=Exception,
       retry=2,
       fallback=lambda user_id: get_cached_profile(user_id),
       reraise=False,
   )
   def get_profile(user_id):
       ...


8. Monitor with Diagnostics
===========================

Run :func:`tranq.render_diagnostics` periodically:

.. code-block:: python

   @app.get("/health")
   def health():
       return {"resilience": tranq.diagnostics()}


9. Use Policy Presets Where Appropriate
========================================

Don't reinvent the wheel:

.. code-block:: python

   from tranq import presets, resilient

   @resilient(**presets.http())
   def fetch_users(): ...

   @resilient(**presets.database())
   def run_query(): ...


10. Test Resilience with Chaos
===============================

Periodically inject failures in staging:

.. code-block:: python

   with tranq.chaos(error_rate=0.2, latency=0.3):
       for _ in range(1000):
           call_service()

   print(tranq.render_diagnostics())
