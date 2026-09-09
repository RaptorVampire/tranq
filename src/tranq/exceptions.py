class TranqError(Exception):
    """Base exception for all tranq errors."""
    pass


class RetryExhaustedError(TranqError):
    """Raised when all retries are exhausted and reraise=True."""
    pass


class CircuitBreakerError(TranqError):
    """Raised when circuit breaker is open."""
    pass


class ResultNotAcceptedError(TranqError):
    """Raised when retry_on_result condition is not met after all attempts."""
    pass


class RetryGroupError(TranqError):
    """Raised when retry_group encounters an error in any member."""
    pass


class FunctionTimeoutError(TranqError, TimeoutError):
    """Raised when a wrapped function exceeds its configured timeout."""
    pass


class RateLimitExceeded(TranqError):
    """Raised when a rate limiter rejects a call."""
    pass


class BulkheadFullError(TranqError):
    """Raised when a bulkhead is at capacity and times out."""
    pass


class RetryBudgetExhaustedError(TranqError):
    """Raised when the retry budget is exhausted and a retry is rejected."""
    pass
