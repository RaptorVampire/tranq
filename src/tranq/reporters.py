import abc
import json
import datetime
import logging
import os


class Reporter(abc.ABC):
    @abc.abstractmethod
    def report(self, exception: BaseException, context: dict):
        """Report an exception with its context."""
        ...


class FileReporter(Reporter):
    """Reporter that writes error details to a file as JSON lines."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        dirname = os.path.dirname(file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    def report(self, exception: BaseException, context: dict):
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "function": context.get("func", "unknown"),
            "exception_type": exception.__class__.__name__,
            "exception_message": str(exception),
            "attempt": context.get("attempt", 1),
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


class LogReporter(Reporter):
    """Reporter that emits errors through the standard logging system."""

    def __init__(self, logger_name: str = "tranq.errors", level: int = logging.ERROR):
        self.logger = logging.getLogger(logger_name)
        self.level = level

    def report(self, exception: BaseException, context: dict):
        func = context.get("func", "unknown")
        attempt = context.get("attempt", 1)
        self.logger.log(self.level, "[%s] %s: %s (attempt %s)",
                        func, exception.__class__.__name__, exception, attempt)


class PrometheusReporter(Reporter):
    """Reporter exposing error counts as Prometheus counters.

    Uses prometheus_client when available; otherwise keeps in-memory counts.
    """

    def __init__(self, prefix: str = "tranq"):
        self.prefix = prefix
        self._counter = None
        self._counts = {}
        try:
            from prometheus_client import Counter
            self._counter = Counter(
                f"{prefix}_errors_total", "Errors reported by tranq", ["function"])
        except Exception:
            self._counter = None

    def report(self, exception: BaseException, context: dict):
        func = context.get("func", "unknown")
        if self._counter is not None:
            try:
                self._counter.labels(function=func).inc()
                return
            except Exception:
                pass
        self._counts[func] = self._counts.get(func, 0) + 1

    def counts(self) -> dict:
        return dict(self._counts)


class SentryReporter(Reporter):
    """Reporter forwarding errors to Sentry (requires sentry_sdk)."""

    def __init__(self, dsn: str = None):
        self.dsn = dsn
        self._sdk = None
        if dsn:
            try:
                import sentry_sdk
                sentry_sdk.init(dsn=dsn)
                self._sdk = sentry_sdk
            except Exception:
                self._sdk = None

    def report(self, exception: BaseException, context: dict):
        if self._sdk is None:
            return
        try:
            self._sdk.capture_exception(exception)
        except Exception:
            pass


class SlackReporter(Reporter):
    """Reporter posting errors to a Slack webhook (requires requests)."""

    def __init__(self, webhook_url: str, channel: str = None, username: str = "tranq"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username

    def report(self, exception: BaseException, context: dict):
        try:
            import requests
        except Exception:
            return
        func = context.get("func", "unknown")
        text = (f":rotating_light: *tranq* error in `{func}`: "
                f"`{exception.__class__.__name__}: {exception}`")
        payload = {"text": text, "username": self.username}
        if self.channel:
            payload["channel"] = self.channel
        try:
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception:
            pass
