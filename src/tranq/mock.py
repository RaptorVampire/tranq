import random
from contextlib import contextmanager
from typing import Type

@contextmanager
def mock_errors(exception: Type[BaseException], probability: float = 0.5):
    class ErrorInjector:
        def raise_if(self):
            if random.random() < probability:
                raise exception("Injected mock error")
    injector = ErrorInjector()
    yield injector
