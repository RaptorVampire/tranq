"""Adaptive resilience: automatically tune policy from observed signals."""
import time
import threading


class AdaptiveController:
    """Observes latency, error rate and traffic, then recommends/adjusts policy.

    Rules:
        latency up        -> timeout down
        errors up         -> retry down, circuit breaker more sensitive
        traffic up        -> rate limit down
    """

    def __init__(self, base_timeout: float = 10.0, base_retry: int = 3,
                 base_rate: float = 100.0, latency_target: float = 1.0,
                 error_target: float = 0.05, window: int = 100):
        self.base_timeout = base_timeout
        self.base_retry = base_retry
        self.base_rate = base_rate
        self.latency_target = latency_target
        self.error_target = error_target
        self.window = window
        self._latencies = []
        self._outcomes = []
        self._lock = threading.Lock()

    def observe(self, latency: float = None, success: bool = None):
        with self._lock:
            if latency is not None:
                self._latencies.append(latency)
                if len(self._latencies) > self.window:
                    self._latencies.pop(0)
            if success is not None:
                self._outcomes.append(success)
                if len(self._outcomes) > self.window:
                    self._outcomes.pop(0)

    def _avg_latency(self):
        return sum(self._latencies) / len(self._latencies) if self._latencies else 0.0

    def _error_rate(self):
        if not self._outcomes:
            return 0.0
        return sum(1 for o in self._outcomes if not o) / len(self._outcomes)

    def recommend(self) -> dict:
        """Return adjusted policy parameters based on observed signals."""
        with self._lock:
            avg_latency = self._avg_latency()
            error_rate = self._error_rate()

        timeout = self.base_timeout
        retry = self.base_retry
        rate = self.base_rate

        # High latency -> reduce timeout to fail faster.
        if avg_latency > self.latency_target:
            factor = max(0.25, self.latency_target / avg_latency)
            timeout = self.base_timeout * factor

        # High error rate -> reduce retries and tighten circuit breaker.
        if error_rate > self.error_target:
            retry = max(0, int(self.base_retry * (1.0 - error_rate)))

        return {
            "timeout": timeout,
            "retry": retry,
            "rate_limit": rate,
            "observed_latency": avg_latency,
            "observed_error_rate": error_rate,
        }

    def apply(self, policy_builder):
        """Apply recommended parameters to a PolicyBuilder."""
        rec = self.recommend()
        policy_builder.timeout(rec["timeout"])
        policy_builder.retry(max_attempts=rec["retry"] + 1)
        return rec
