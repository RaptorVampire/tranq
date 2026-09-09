"""Unified event bus for resilience lifecycle events."""
from collections import defaultdict


class TranqEvent:
    """Base class for all tranq events."""
    name = "event"

    def __init__(self, **data):
        self.data = data

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.data}>"


class RetryStarted(TranqEvent): name = "retry.started"
class RetryCompleted(TranqEvent): name = "retry.completed"
class CircuitOpened(TranqEvent): name = "circuit.opened"
class CircuitClosed(TranqEvent): name = "circuit.closed"
class CircuitHalfOpened(TranqEvent): name = "circuit.half_opened"
class TimeoutTriggered(TranqEvent): name = "timeout.triggered"
class RateLimitExceededEvent(TranqEvent): name = "rate_limit.exceeded"
class BulkheadRejectedEvent(TranqEvent): name = "bulkhead.rejected"
class FallbackTriggered(TranqEvent): name = "fallback.triggered"
class CacheHitEvent(TranqEvent): name = "cache.hit"
class CacheMissEvent(TranqEvent): name = "cache.miss"
class HedgeStarted(TranqEvent): name = "hedge.started"
class OperationSucceeded(TranqEvent): name = "operation.succeeded"
class OperationFailed(TranqEvent): name = "operation.failed"


class EventBus:
    """Publish/subscribe hub for resilience events.

    Usage:
        bus = EventBus()
        bus.subscribe(CircuitOpenedEvent, handler)   # specific event class
        bus.subscribe("*", handler)                  # all events
        bus.publish(CircuitOpenedEvent(breaker="db"))
    """

    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, event_type, handler):
        key = "*" if event_type == "*" else event_type
        self._handlers[key].append(handler)
        return handler

    def unsubscribe(self, event_type, handler):
        key = "*" if event_type == "*" else event_type
        if handler in self._handlers[key]:
            self._handlers[key].remove(handler)

    def publish(self, event):
        cls = type(event)
        for handler in self._handlers.get(cls, []):
            try:
                handler(event)
            except Exception:
                pass
        for handler in self._handlers.get("*", []):
            try:
                handler(event)
            except Exception:
                pass

    def clear(self):
        self._handlers.clear()


# Convenience: a default global bus
_default_bus = EventBus()


def get_default_event_bus() -> EventBus:
    return _default_bus


def subscribe(event_type, handler):
    return _default_bus.subscribe(event_type, handler)


def publish(event):
    _default_bus.publish(event)
