"""Timeout helpers: deadlines, per-attempt and total-operation timeouts."""
import time


class Deadline:
    """Represents an absolute point in time by which an operation must finish."""

    def __init__(self, seconds: float):
        self._end = time.monotonic() + seconds
        self.total = seconds

    def remaining(self) -> float:
        return max(0.0, self._end - time.monotonic())

    def expired(self) -> bool:
        return time.monotonic() >= self._end

    def __float__(self):
        return self.remaining()


class DeadlineExceededError(Exception):
    """Raised when an operation exceeds its overall deadline."""
    pass


def per_attempt_timeout(func, timeout, args=(), kwargs=None):
    """Run a sync function with a timeout applied to each attempt."""
    from .utils import run_with_timeout
    return run_with_timeout(func, args, kwargs or {}, timeout)


def check_deadline(deadline: Deadline):
    """Raise DeadlineExceededError if the deadline has passed."""
    if deadline is not None and deadline.expired():
        raise DeadlineExceededError("Operation deadline exceeded")
