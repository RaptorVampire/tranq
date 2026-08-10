"""Example 02: Retry strategies — exponential, linear, fibonacci, custom."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import time as _time
import tranq

# Capture sleep calls instead of actually sleeping
recorded_delays = []
original_sleep = _time.sleep
_time.sleep = lambda t: recorded_delays.append(t)

try:
    # Exponential backoff: delay * backoff ** attempt
    @tranq.handle(on=ValueError, retry=3, delay=0.1, backoff=2.0,
                  backoff_strategy="exponential", jitter=False)
    def exponential_demo():
        raise ValueError("fail")

    try:
        exponential_demo()
    except ValueError:
        pass
    print("Exponential delays:", recorded_delays)
    recorded_delays.clear()

    # Linear backoff: delay + delay * attempt
    @tranq.handle(on=ValueError, retry=3, delay=0.1,
                  backoff_strategy="linear", jitter=False)
    def linear_demo():
        raise ValueError("fail")

    try:
        linear_demo()
    except ValueError:
        pass
    print("Linear delays:", recorded_delays)
    recorded_delays.clear()

    # Fibonacci backoff: delay * fib(attempt)
    @tranq.handle(on=ValueError, retry=5, delay=0.1,
                  backoff_strategy="fibonacci", jitter=False)
    def fibonacci_demo():
        raise ValueError("fail")

    try:
        fibonacci_demo()
    except ValueError:
        pass
    print("Fibonacci delays:", recorded_delays)
    recorded_delays.clear()

    # Custom callable backoff
    @tranq.handle(on=ValueError, retry=3, delay=1.0,
                  backoff_strategy=lambda attempt: attempt * 1.5, jitter=False)
    def custom_demo():
        raise ValueError("fail")

    try:
        custom_demo()
    except ValueError:
        pass
    print("Custom delays:", recorded_delays)
    recorded_delays.clear()

    # max_delay caps the wait time
    @tranq.handle(on=ValueError, retry=3, delay=1.0, backoff=10.0,
                  max_delay=2.0, jitter=False)
    def max_delay_demo():
        raise ValueError("fail")

    try:
        max_delay_demo()
    except ValueError:
        pass
    print("Capped delays (max_delay=2.0):", recorded_delays)
    recorded_delays.clear()

    # Jitter adds randomness
    @tranq.handle(on=ValueError, retry=5, delay=1.0,
                  backoff_strategy=lambda a: 1.0, jitter=True)
    def jitter_demo():
        raise ValueError("fail")

    try:
        jitter_demo()
    except ValueError:
        pass
    print("Jittered delays (each between 0.75 and 1.25):", recorded_delays)

finally:
    _time.sleep = original_sleep
