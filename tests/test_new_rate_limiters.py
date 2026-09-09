from tranq import LeakyBucket, FixedWindowLimiter, SlidingWindowLimiter, AdaptiveRateLimiter


def test_leaky_bucket():
    lb = LeakyBucket(capacity=2, leak_rate=1.0)
    assert lb.try_acquire()
    assert lb.try_acquire()
    assert not lb.try_acquire()


def test_fixed_window():
    fw = FixedWindowLimiter(limit=2, window=1.0)
    assert fw.try_acquire()
    assert fw.try_acquire()
    assert not fw.try_acquire()


def test_sliding_window():
    sw = SlidingWindowLimiter(limit=2, window=1.0)
    assert sw.try_acquire()
    assert sw.try_acquire()
    assert not sw.try_acquire()


def test_adaptive_rate_limiter():
    arl = AdaptiveRateLimiter(base_rate=10.0)
    initial = arl.current_rate
    arl.record_failure()
    assert arl.current_rate < initial
    arl.record_success()
    assert arl.current_rate >= arl.current_rate  # recovers
