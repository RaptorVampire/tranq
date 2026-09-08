"""tranq - Calm error handling for Python."""

__version__ = "1.0.0"
__author__ = "RaptorVampire <mhman884@gmail.com>"

from .decorators import handle, handle_async
from .exceptions import (
    TranqError,
    RetryExhaustedError,
    CircuitBreakerError,
    ResultNotAcceptedError,
    RetryGroupError,
    FunctionTimeoutError,
    RateLimitExceeded,
    BulkheadFullError,
    RetryBudgetExhaustedError,
)
from .policies import Policy, set_global_policy, get_global_policy
from .circuit_breaker import CircuitBreaker
from .async_circuit_breaker import AsyncCircuitBreaker
from .sliding_window import SlidingWindowCircuitBreaker, AsyncSlidingWindowCircuitBreaker
from .context import retry, retry_async
from .retry_group import retry_group, async_retry_group
from .reporters import (
    Reporter, FileReporter, SentryReporter, SlackReporter,
    LogReporter, PrometheusReporter,
)
from .metrics import get_metrics, reset_metrics
from .profiling import profile, get_profile, async_profile
from .mock import mock_errors
from .rate_limiter import RateLimiter, rate_limit
from .bulkhead import Bulkhead, AsyncBulkhead, bulkhead
from .retry_budget import RetryBudget, get_default_retry_budget, set_default_retry_budget
from .hedge import hedged_call, hedged
from .statistics import summary_table, overall_health, render_report

__all__ = [
    "handle", "handle_async", "retry", "retry_async",
    "retry_group", "async_retry_group",
    "TranqError", "RetryExhaustedError", "CircuitBreakerError",
    "ResultNotAcceptedError", "RetryGroupError", "FunctionTimeoutError",
    "RateLimitExceeded", "BulkheadFullError", "RetryBudgetExhaustedError",
    "Policy", "set_global_policy", "get_global_policy",
    "CircuitBreaker", "AsyncCircuitBreaker",
    "SlidingWindowCircuitBreaker", "AsyncSlidingWindowCircuitBreaker",
    "Reporter", "FileReporter", "SentryReporter", "SlackReporter",
    "LogReporter", "PrometheusReporter",
    "get_metrics", "reset_metrics", "profile", "get_profile", "async_profile",
    "mock_errors", "RateLimiter", "rate_limit", "Bulkhead", "AsyncBulkhead",
    "bulkhead", "RetryBudget", "get_default_retry_budget", "set_default_retry_budget",
    "hedged_call", "hedged", "summary_table", "overall_health", "render_report",
]
