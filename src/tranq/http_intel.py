"""HTTP intelligence: retryable status detection and Retry-After parsing."""
import time

RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


def extract_status(exception) -> int:
    """Extract an HTTP status code from an exception, if present."""
    resp = getattr(exception, "response", None)
    if resp is not None and hasattr(resp, "status_code"):
        return resp.status_code
    for attr in ("status_code", "status"):
        v = getattr(exception, attr, None)
        if isinstance(v, int):
            return v
    return None


def is_retryable_status(status) -> bool:
    return status in RETRYABLE_STATUS


def is_retryable(exception) -> bool:
    status = extract_status(exception)
    return status is not None and is_retryable_status(status)


def parse_retry_after(exception) -> float:
    """Parse a Retry-After value (seconds or HTTP-date) from an exception.

    Returns the number of seconds to wait, or 0 if unavailable.
    """
    retry_after = getattr(exception, "retry_after", None)
    if retry_after is not None:
        try:
            return float(retry_after)
        except (TypeError, ValueError):
            pass

    resp = getattr(exception, "response", None)
    headers = getattr(resp, "headers", None) if resp is not None else None
    if headers is None:
        return 0.0

    value = headers.get("Retry-After") or headers.get("retry-after")
    if value is None:
        # Try rate-limit reset headers (epoch seconds).
        reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
        if reset is not None:
            try:
                return max(0.0, float(reset) - time.time())
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        # Possibly an HTTP-date; fall back to a conservative default.
        return 1.0


def recommended_wait(exception, default: float = 1.0) -> float:
    """Recommended wait time for an HTTP exception, honoring Retry-After."""
    ra = parse_retry_after(exception)
    return ra if ra > 0 else default
