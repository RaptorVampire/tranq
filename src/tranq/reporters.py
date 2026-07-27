import abc
import datetime
import os

class Reporter(abc.ABC):
    @abc.abstractmethod
    def report(self, exception: BaseException, context: dict):
        """Report an exception with its context."""
        ...

class FileReporter(Reporter):
    """Reporter that writes error details to a file."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        # فقط اگر دایرکتوری والد وجود نداشته باشد، آن را ایجاد کن
        dirname = os.path.dirname(file_path)
        if dirname:  # اگر رشته خالی نباشد
            os.makedirs(dirname, exist_ok=True)

    def report(self, exception: BaseException, context: dict):
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(
                f"{datetime.datetime.now().isoformat()} | "
                f"{context.get('func', 'unknown')} | "
                f"{exception.__class__.__name__}: {exception}\n"
            )

class SentryReporter(Reporter):
    """Placeholder for Sentry error reporting."""
    def __init__(self, dsn: str):
        self.dsn = dsn

    def report(self, exception: BaseException, context: dict):
        # در اینجا می‌توانید کد واقعی ارسال به سنتری را پیاده‌سازی کنید
        pass

class SlackReporter(Reporter):
    """Placeholder for Slack webhook reporting."""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def report(self, exception: BaseException, context: dict):
        # در اینجا می‌توانید کد واقعی ارسال به اسلک را پیاده‌سازی کنید
        pass