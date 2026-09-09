from tranq import EventBus
from tranq.events import CircuitOpened, OperationSucceeded


def test_subscribe_publish():
    bus = EventBus()
    received = []
    bus.subscribe(CircuitOpened, lambda e: received.append(e))
    bus.publish(CircuitOpened(breaker="db"))
    assert len(received) == 1
    assert received[0].data["breaker"] == "db"


def test_wildcard_subscription():
    bus = EventBus()
    received = []
    bus.subscribe("*", lambda e: received.append(type(e).__name__))
    bus.publish(CircuitOpened(breaker="a"))
    bus.publish(OperationSucceeded(func="f"))
    assert received == ["CircuitOpened", "OperationSucceeded"]


def test_unsubscribe():
    bus = EventBus()
    received = []
    h = bus.subscribe(CircuitOpened, lambda e: received.append(e))
    bus.unsubscribe(CircuitOpened, h)
    bus.publish(CircuitOpened(breaker="x"))
    assert received == []
