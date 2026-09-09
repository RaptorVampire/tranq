"""tranq - Calm, production-grade error handling & resilience for Python."""

__version__ = "1.1.0"
__author__ = "RaptorVampire <mhman884@gmail.com>"

# Core decorators
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
from .circuit_breaker import CircuitBreaker, BreakerRegistry, get_registry
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
from .rate_limiter import (
    RateLimiter, rate_limit, LeakyBucket, FixedWindowLimiter,
    SlidingWindowLimiter, AdaptiveRateLimiter,
)
from .bulkhead import Bulkhead, AsyncBulkhead, bulkhead, QueueBulkhead, KeyedBulkhead
from .retry_budget import RetryBudget, get_default_retry_budget, set_default_retry_budget
from .hedge import hedged_call, hedged, hedged_quorum, PercentileHedgeDelay
from .statistics import summary_table, overall_health, render_report

# Retry primitives
from .wait import wait
from .stop import stop
from .retry_predicates import retry_if

# New platform modules
from .timeout import Deadline, DeadlineExceededError
from .cache import TranqCache, AsyncTranqCache, cache, make_key
from .fallback import FallbackChain, CachedFallback, ConditionalFallback
from .events import EventBus, get_default_event_bus, subscribe, publish
from .adaptive import AdaptiveController
from .presets import presets
from .http_intel import is_retryable, is_retryable_status, parse_retry_after, recommended_wait
from .diagnostics import diagnostics, render_diagnostics
from .chaos import chaos, ChaosInjector, chaos_wrapped, chaos_report, reset_chaos_reports
from .telemetry import Telemetry, telemetry, OTEL_AVAILABLE
from .distributed import (
    StateBackend, InMemoryBackend, RedisBackend,
    DistributedRateLimiter, DistributedCounter,
)
from .dependency import DependencyGraph
from .llm import llm
from .auto import auto, recommend_policy
from .composition import PolicyBuilder, ResiliencePolicy, resilient

__all__ = [
    # core
    "handle", "handle_async", "retry", "retry_async",
    "retry_group", "async_retry_group",
    # exceptions
    "TranqError", "RetryExhaustedError", "CircuitBreakerError",
    "ResultNotAcceptedError", "RetryGroupError", "FunctionTimeoutError",
    "RateLimitExceeded", "BulkheadFullError", "RetryBudgetExhaustedError",
    # policy
    "Policy", "set_global_policy", "get_global_policy",
    # circuit breakers
    "CircuitBreaker", "AsyncCircuitBreaker", "BreakerRegistry", "get_registry",
    "SlidingWindowCircuitBreaker", "AsyncSlidingWindowCircuitBreaker",
    # reporters
    "Reporter", "FileReporter", "SentryReporter", "SlackReporter",
    "LogReporter", "PrometheusReporter",
    # metrics / profiling
    "get_metrics", "reset_metrics", "profile", "get_profile", "async_profile",
    "summary_table", "overall_health", "render_report",
    # mock
    "mock_errors",
    # rate limiting
    "RateLimiter", "rate_limit", "LeakyBucket", "FixedWindowLimiter",
    "SlidingWindowLimiter", "AdaptiveRateLimiter",
    # bulkhead
    "Bulkhead", "AsyncBulkhead", "bulkhead", "QueueBulkhead", "KeyedBulkhead",
    # retry budget
    "RetryBudget", "get_default_retry_budget", "set_default_retry_budget",
    # hedge
    "hedged_call", "hedged", "hedged_quorum", "PercentileHedgeDelay",
    # retry primitives
    "wait", "stop", "retry_if",
    # timeout
    "Deadline", "DeadlineExceededError",
    # cache
    "TranqCache", "AsyncTranqCache", "cache", "make_key",
    # fallback
    "FallbackChain", "CachedFallback", "ConditionalFallback",
    # events
    "EventBus", "get_default_event_bus", "subscribe", "publish",
    # adaptive / presets / http
    "AdaptiveController", "presets",
    "is_retryable", "is_retryable_status", "parse_retry_after", "recommended_wait",
    # diagnostics / chaos
    "diagnostics", "render_diagnostics",
    "chaos", "ChaosInjector", "chaos_wrapped", "chaos_report", "reset_chaos_reports",
    # telemetry
    "Telemetry", "telemetry", "OTEL_AVAILABLE",
    # distributed
    "StateBackend", "InMemoryBackend", "RedisBackend",
    "DistributedRateLimiter", "DistributedCounter",
    # dependency / llm / auto
    "DependencyGraph", "llm", "auto", "recommend_policy",
    # composition
    "PolicyBuilder", "ResiliencePolicy", "resilient",
]
