import abc
import json
import datetime
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

class SentryReporter(Reporter):
    """Placeholder for Sentry error reporting."""
    def __init__(self, dsn: str):
        self.dsn = dsn

    def report(self, exception: BaseException, context: dict):
        pass

class SlackReporter(Reporter):
    """Placeholder for Slack webhook reporting."""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def report(self, exception: BaseException, context: dict):
        pass
