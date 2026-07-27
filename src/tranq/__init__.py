"""tranq - Calm error handling for Python."""

__version__ = "0.2.7"
__author__ = "RaptorVampire <mhman884@gmail.com>"

from .decorators import handle, handle_async
from .exceptions import (
    TranqError,
    RetryExhaustedError,
    CircuitBreakerError,
    ResultNotAcceptedError,
    RetryGroupError,
)
from .policies import Policy, set_global_policy, get_global_policy
from .circuit_breaker import CircuitBreaker
from .async_circuit_breaker import AsyncCircuitBreaker
from .context import retry
from .retry_group import retry_group, async_retry_group
from .reporters import Reporter, FileReporter, SentryReporter, SlackReporter
from .metrics import get_metrics, reset_metrics
from .profiling import profile, get_profile
from .mock import mock_errors

__all__ = [
    "handle",
    "handle_async",
    "retry",
    "retry_group",
    "async_retry_group",
    "TranqError",
    "RetryExhaustedError",
    "CircuitBreakerError",
    "ResultNotAcceptedError",
    "RetryGroupError",
    "Policy",
    "set_global_policy",
    "get_global_policy",
    "CircuitBreaker",
    "AsyncCircuitBreaker",
    "Reporter",
    "FileReporter",
    "SentryReporter",
    "SlackReporter",
    "get_metrics",
    "reset_metrics",
    "profile",
    "get_profile",
    "mock_errors",
]