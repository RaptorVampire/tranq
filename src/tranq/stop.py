"""Stop conditions. Each stop is a callable: stop(attempt, elapsed) -> bool.

Composable with ``&`` (AND / all) and ``|`` (OR / any).
"""


class stop_base:
    def __call__(self, attempt: int, elapsed: float) -> bool:
        raise NotImplementedError

    def __and__(self, other):
        return stop_all(self, other)

    def __or__(self, other):
        return stop_any(self, other)


class stop_never(stop_base):
    """Never stop (infinite retry)."""

    def __call__(self, attempt, elapsed):
        return False


class stop_after_attempt(stop_base):
    """Stop after a maximum number of attempts."""

    def __init__(self, max_attempt: int):
        self.max_attempt = max_attempt

    def __call__(self, attempt, elapsed):
        return attempt >= self.max_attempt


class stop_after_delay(stop_base):
    """Stop after a total elapsed time (seconds)."""

    def __init__(self, max_delay: float):
        self.max_delay = max_delay

    def __call__(self, attempt, elapsed):
        return elapsed >= self.max_delay


class stop_before_deadline(stop_base):
    """Stop if the next attempt is expected to exceed the deadline.

    ``expected_next`` estimates the duration of the upcoming attempt.
    """

    def __init__(self, deadline: float, expected_next: float = 0.0):
        self.deadline = deadline
        self.expected_next = expected_next

    def __call__(self, attempt, elapsed):
        return (elapsed + self.expected_next) >= self.deadline


class stop_when(stop_base):
    """Stop when an arbitrary predicate(attempt, elapsed) returns True."""

    def __init__(self, predicate):
        self.predicate = predicate

    def __call__(self, attempt, elapsed):
        return self.predicate(attempt, elapsed)


class stop_all(stop_base):
    """Logical AND: stop only when every condition says stop."""

    def __init__(self, *stops):
        self.stops = stops

    def __call__(self, attempt, elapsed):
        return all(s(attempt, elapsed) for s in self.stops)


class stop_any(stop_base):
    """Logical OR: stop when any condition says stop."""

    def __init__(self, *stops):
        self.stops = stops

    def __call__(self, attempt, elapsed):
        return any(s(attempt, elapsed) for s in self.stops)


class stop:
    """Namespace with factory helpers."""
    never = stop_never
    after_attempt = stop_after_attempt
    after_delay = stop_after_delay
    before_deadline = stop_before_deadline
    when = stop_when
    all = stop_all
    any = stop_any
