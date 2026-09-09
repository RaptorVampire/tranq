.. _design:

==============
Design & Philosophy
==============

tranq is built on a small set of powerful ideas that compose cleanly.

The Retry Lifecycle
===================

Every decorated function follows the same well-defined lifecycle:

.. code-block:: text

   ┌──────────────────────────────────────────────────────────────┐
   │  1. Function called                                          │
   │  2. Cache lookup (if enabled)                                │
   │  3. Rate limiter consulted                                   │
   │  4. Bulkhead acquired                                        │
   │  5. Circuit breaker checked                                  │
   │  6. Retry budget consulted                                   │
   │  7. Function executed (with timeout if configured)           │
   │     ├── Success                                              │
   │     │    → store in cache                                    │
   │     │    → record CB success                                 │
   │     │    → emit OperationSucceeded event                     │
   │     │    → call on_success hook                              │
   │     │    → return result                                     │
   │     └── Exception caught (matches ``on``)                    │
   │         ├── on_error handler matched? → execute, finalize    │
   │         ├── retry_if predicate False?  → finalize (no retry) │
   │         ├── retry_budget rejects?      → finalize            │
   │         ├── stop condition True?       → finalize            │
   │         ├── attempts remaining?                              │
   │         │    → emit RetryStarted event                       │
   │         │    → call on_retry hook                            │
   │         │    → sleep (wait strategy)                         │
   │         │    → GOTO 7                                        │
   │         └── exhausted                                        │
   │              → try cache stale-if-error                      │
   │              → try fallback chain                            │
   │              → emit FallbackTriggered event                  │
   │              → finalize (raise or return)                    │
   │  8. Release bulkhead slot                                    │
   │  9. Call on_complete hook (always)                           │
   └──────────────────────────────────────────────────────────────┘

This lifecycle is the same whether you use ``@handle``, ``@handle_async``,
``tranq.retry(...)`` or ``PolicyBuilder``.


Backoff Strategies
==================

tranq supports every strategy you will ever need, and they compose:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Strategy
     - Formula
     - Use when
   * - :func:`~tranq.wait.fixed`
     - ``c``
     - Rate-limited endpoints with a fixed cool-down.
   * - :func:`~tranq.wait.exponential`
     - ``m × b^a``
     - Most common; spreads retries over time.
   * - :func:`~tranq.wait.fibonacci`
     - ``m × fib(a)``
     - Slower growth than exponential; good default.
   * - :func:`~tranq.wait.linear`
     - ``m + inc × a``
     - Predictable, linear growth.
   * - :func:`~tranq.wait.full_jitter`
     - ``U(0, exp)``
     - Best for high-concurrency (eliminates thundering herd).
   * - :func:`~tranq.wait.equal_jitter`
     - ``exp/2 + U(0, exp/2)``
     - Balances speed and herd avoidance.
   * - :func:`~tranq.wait.decorrelate_jitter`
     - AWS-style decorrelated
     - Long-running jobs with variance.


Stop Conditions
===============

Stop conditions are composable with ``&`` (AND) and ``|`` (OR):

.. code-block:: python

   from tranq import stop

   policy = (
       PolicyBuilder()
       .retry(
           stop=stop.after_attempt(5) | stop.after_delay(30)
       )
   )

This stops as soon as **either** 5 attempts have been made **or** 30 seconds
have elapsed.


Retry Predicates
================

Predicates decide whether a failure is worth retrying:

.. code-block:: python

   from tranq import retry_if

   should_retry = (
       retry_if.http_status((429, 503)) |
       retry_if.exception_type(ConnectionError)
   )

   @tranq.handle(on=Exception, retry_if=should_retry, retry=3)
   def call_api():
       ...

Composition via ``&`` and ``|`` makes the intent explicit and self-documenting.


State Isolation
===============

tranq uses :class:`contextvars.ContextVar` to isolate per-call state:

* Each thread gets its own attempt counter
* Each asyncio task gets its own attempt counter
* Stateful retry persists counters across calls in the same context
* No cross-contamination between concurrent executions

This means you can safely wrap every function in a web server and
tranq will never confuse request A with request B.


Thread & Async Safety
=====================

All mutable state is protected:

* :class:`~tranq.CircuitBreaker` uses :class:`threading.Lock`
* :class:`~tranq.AsyncCircuitBreaker` uses :class:`asyncio.Lock`
* Metrics and profiles use :class:`threading.Lock`
* Rate limiters and bulkheads are thread-safe
* Cache is thread-safe (async variant for asyncio)

You can share instances across threads or tasks without additional
synchronization.
