.. _feature-events:

==========
Event Bus
==========

tranq emits structured events for every resilience operation. Subscribe with
:class:`~tranq.EventBus` and react in real time.


Event Types
===========

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Event
     - Fired when
   * - :class:`~tranq.events.RetryStarted`
     - A retry is about to sleep
   * - :class:`~tranq.events.RetryCompleted`
     - A retry attempt has finished
   * - :class:`~tranq.events.CircuitOpened`
     - A circuit breaker transitions to open
   * - :class:`~tranq.events.CircuitClosed`
     - A circuit breaker transitions to closed
   * - :class:`~tranq.events.CircuitHalfOpened`
     - A circuit breaker transitions to half-open
   * - :class:`~tranq.events.TimeoutTriggered`
     - A timeout fires
   * - :class:`~tranq.events.RateLimitExceededEvent`
     - A rate limiter rejects a call
   * - :class:`~tranq.events.BulkheadRejectedEvent`
     - A bulkhead is at capacity
   * - :class:`~tranq.events.FallbackTriggered`
     - A fallback is invoked
   * - :class:`~tranq.events.CacheHitEvent`
     - A cache lookup succeeded
   * - :class:`~tranq.events.CacheMissEvent`
     - A cache lookup missed
   * - :class:`~tranq.events.HedgeStarted`
     - A hedge request is launched
   * - :class:`~tranq.events.OperationSucceeded`
     - A decorated call succeeded
   * - :class:`~tranq.events.OperationFailed`
     - A decorated call failed


Subscribe
=========

.. code-block:: python

   from tranq import EventBus, events

   bus = EventBus()

   # Specific event
   bus.subscribe(events.CircuitOpened,
                 lambda e: alert(f"CB {e.data['breaker']} opened"))

   # Wildcard: all events
   bus.subscribe("*", lambda e: log(e))


Wire into Policies
==================

.. code-block:: python

   policy = (
       tranq.PolicyBuilder()
       .retry(max_attempts=3)
       .circuit_breaker(cb)
       .observe(event_bus=bus)
   )


Default Global Bus
==================

.. code-block:: python

   from tranq import subscribe, publish, events

   subscribe(events.CircuitOpened, handler)
   publish(events.CircuitOpened(breaker="db"))


See Also
========

* :doc:`../api/events`
* :doc:`circuit_breaker` — emit state-change events
