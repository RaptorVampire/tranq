import random
from contextlib import contextmanager
from typing import Type

@contextmanager
def mock_errors(exception: Type[BaseException], probability: float = 0.5, seed: int = None):
    """Context manager that injects the given exception with the specified probability.
    If seed is provided, random generator is seeded for reproducibility.
    """
    rng = random.Random(seed) if seed is not None else random
    try:
        yield
    except exception:
        raise
    else:
        if rng.random() < probability:
            raise exception("Injected mock error")
