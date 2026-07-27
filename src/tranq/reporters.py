import abc
import datetime
import os

class Reporter(abc.ABC):
    @abc.abstractmethod
    def report(self, exception: BaseException, context: dict):
        ...

class FileReporter(Reporter):
    def __init__(self, file_path: str):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def report(self, exception: BaseException, context: dict):
        with open(self.file_path, "a") as f:
            f.write(f"{datetime.datetime.now()}: {context.get('func','')} error: {exception}\n")

class SentryReporter(Reporter):
    def __init__(self, dsn: str):
        self.dsn = dsn

    def report(self, exception: BaseException, context: dict):
        pass

class SlackReporter(Reporter):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def report(self, exception: BaseException, context: dict):
        pass
