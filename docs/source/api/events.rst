Event Bus
=========

.. automodule:: tranq.events
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: tranq.EventBus
   :members:

.. autoclass:: tranq.events.TranqEvent
.. autoclass:: tranq.events.RetryStarted
.. autoclass:: tranq.events.RetryCompleted
.. autoclass:: tranq.events.CircuitOpened
.. autoclass:: tranq.events.CircuitClosed
.. autoclass:: tranq.events.CircuitHalfOpened
.. autoclass:: tranq.events.TimeoutTriggered
.. autoclass:: tranq.events.RateLimitExceededEvent
.. autoclass:: tranq.events.BulkheadRejectedEvent
.. autoclass:: tranq.events.FallbackTriggered
.. autoclass:: tranq.events.CacheHitEvent
.. autoclass:: tranq.events.CacheMissEvent
.. autoclass:: tranq.events.HedgeStarted
.. autoclass:: tranq.events.OperationSucceeded
.. autoclass:: tranq.events.OperationFailed

.. autofunction:: tranq.get_default_event_bus
.. autofunction:: tranq.subscribe
.. autofunction:: tranq.publish
