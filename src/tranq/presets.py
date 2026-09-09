"""Ready-made resilience presets for common backends."""
"""Ready-made resilience presets for common backends.

Each preset returns a config dict with composable building blocks:
    wait     -- a wait strategy instance
    stop     -- a stop condition instance
    retry_if -- a retry predicate (or None)
    timeout  -- per-attempt timeout in seconds (or None)
"""
from .wait import wait_exponential, wait_random_exponential, wait_fixed
from .stop import stop_after_attempt, stop_after_delay
from .retry_predicates import retry_if_http_status, retry_if_retry_after


def _base():
    return {
        "wait": wait_exponential(multiplier=0.5, max=30.0),
        "stop": stop_after_attempt(3),
        "retry_if": None,
        "timeout": None,
    }


def http():
    """HTTP client preset: retry on 429/5xx with jittered exponential backoff."""
    cfg = _base()
    cfg["wait"] = wait_random_exponential(multiplier=0.5, max=20.0)
    cfg["stop"] = stop_after_attempt(4) | stop_after_delay(30.0)
    cfg["retry_if"] = retry_if_http_status((429, 500, 502, 503, 504))
    cfg["timeout"] = 10.0
    return cfg


def database():
    """Database preset: conservative retries, short timeout."""
    cfg = _base()
    cfg["wait"] = wait_exponential(multiplier=0.2, max=5.0)
    cfg["stop"] = stop_after_attempt(3)
    cfg["timeout"] = 5.0
    return cfg


def redis():
    """Redis/cache preset: fast fail, minimal retries."""
    cfg = _base()
    cfg["wait"] = wait_fixed(0.05)
    cfg["stop"] = stop_after_attempt(2)
    cfg["timeout"] = 1.0
    return cfg


def kafka():
    """Message queue preset: more retries, longer backoff."""
    cfg = _base()
    cfg["wait"] = wait_exponential(multiplier=1.0, max=60.0)
    cfg["stop"] = stop_after_attempt(5) | stop_after_delay(120.0)
    return cfg


def queue():
    return kafka()


def grpc():
    """gRPC preset."""
    cfg = _base()
    cfg["wait"] = wait_random_exponential(multiplier=0.3, max=15.0)
    cfg["stop"] = stop_after_attempt(4)
    cfg["timeout"] = 15.0
    return cfg


def llm():
    """LLM API preset: handle rate limits, longer timeouts."""
    cfg = _base()
    cfg["wait"] = wait_random_exponential(multiplier=1.0, max=60.0)
    cfg["stop"] = stop_after_attempt(5) | stop_after_delay(180.0)
    cfg["retry_if"] = retry_if_http_status((429, 500, 502, 503)) | retry_if_retry_after()
    cfg["timeout"] = 60.0
    return cfg


class presets:
    """Namespace for preset factories."""
    http = staticmethod(http)
    database = staticmethod(database)
    redis = staticmethod(redis)
    kafka = staticmethod(kafka)
    queue = staticmethod(queue)
    grpc = staticmethod(grpc)
    llm = staticmethod(llm)
