.. _feature-circuit-breaker:

================
Circuit Breakers
================

Circuit breakers prevent cascading failures by stopping calls to a service
that is clearly failing. tranq provides **count-based** and **failure-rate**
(sliding-window) breakers with slow-call detection, event emission, and a
shared registry.


Count-Based Breaker
===================

The classic three-state machine:

.. code-block:: text

   CLOSED ──(failures ≥ threshold)──► OPEN
     ▲                                   │
     │                                   │ (timeout elapsed)
     │                                   ▼
     └──(probe succeeds)── HALF-OPEN ──(probe fails)──► OPEN

.. code-block:: python

   from tranq import CircuitBreaker

   cb = CircuitBreaker(
       failure_threshold=5,     # Open after 5 consecutive failures
       timeout=60.0,            # Wait 60s before probing
       half_open_requests=1,    # Allow 1 probe in half-open
   )

   @tranq.handle(on=Exception, circuit_breaker=cb)
   def call_service():
       ...


Sliding Window Breaker
======================

.. versionadded:: 1.1.0

Opens based on **failure rate** over a sliding window, tolerating sporadic
failures while reacting to sustained degradation.

.. code-block:: python

   from tranq import SlidingWindowCircuitBreaker

   swc = SlidingWindowCircuitBreaker(
       window_size=100,              # Track last 100 outcomes
       failure_rate_threshold=0.5,   # Open if ≥50% fail
       timeout=30.0,                 # Wait 30s before probing
       half_open_requests=3,         # Allow 3 probes
       minimum_calls=10,             # Need 10 samples first
   )

   @tranq.handle(on=Exception, circuit_breaker=swc)
   def unreliable_service():
       ...


Slow-Call Detection
===================

.. versionadded:: 1.1.0

Open the breaker when too many calls are slow, even if they succeed:

.. code-block:: python

   cb = CircuitBreaker(
       failure_threshold=5,
       timeout=60.0,
       slow_call_duration=2.0,        # Calls > 2s are "slow"
       slow_call_rate_threshold=0.5,  # Open if 50% are slow
       minimum_calls=10,
   )


State-Change Events
===================

.. versionadded:: 1.1.0

Breakers emit events to an :class:`~tranq.EventBus`:

.. code-block:: python

   from tranq import EventBus, events

   bus = EventBus()
   bus.subscribe(events.CircuitOpened, lambda e: alert(f"{e.data['breaker']} opened"))
   bus.subscribe(events.CircuitClosed, lambda e: alert(f"{e.data['breaker']} closed"))

   cb = CircuitBreaker(failure_threshold=3, event_bus=bus, name="payment")


Breaker Registry
================

.. versionadded:: 1.1.0

Share named breakers across functions:

.. code-block:: python

   from tranq import get_registry

   registry = get_registry()
   payment_cb = registry.get("payment", failure_threshold=5)
   user_cb    = registry.get("user", failure_threshold=3)

   print(registry.states())
   # {'payment': 'closed', 'user': 'closed'}


When to Use Which
=================

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Use ``CircuitBreaker``
     - Use ``SlidingWindowCircuitBreaker``
   * - Want fast reaction to consecutive failures
     - Want to tolerate sporadic failures
   * - Service is binary (works or doesn't)
     - Service has intermittent degradation
   * - Low traffic
     - High traffic (need statistical significance)
   * - Simplicity preferred
     - Precision matters


Async Support
=============

Every circuit breaker has an async counterpart:

.. code-block:: python

   from tranq import AsyncCircuitBreaker, AsyncSlidingWindowCircuitBreaker

   acb = AsyncCircuitBreaker(failure_threshold=3)

   @tranq.handle_async(on=Exception, circuit_breaker=acb)
   async def call_service():
       ...


See Also
========

* :doc:`../api/circuit_breakers` — full API reference
* :doc:`events` — subscribe to circuit events
