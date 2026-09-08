from tranq import get_metrics, reset_metrics
from tranq.metrics import record_metric

def test_record_and_retrieve():
    reset_metrics()
    record_metric("test", "func1", 0.5, False)
    m = get_metrics()
    assert m["test.func1"]["count"] == 1
    assert m["test.func1"]["total_duration"] == 0.5
    assert m["test.func1"]["errors"] == 0

def test_record_error():
    reset_metrics()
    record_metric("test", "func2", 0.0, True)
    m = get_metrics()
    assert m["test.func2"]["errors"] == 1

def test_reset():
    reset_metrics()
    record_metric("test", "func3", 0.1, False)
    reset_metrics()
    assert get_metrics() == {}

def test_thread_safety():
    import threading
    reset_metrics()
    def worker():
        for _ in range(10):
            record_metric("multi", "f", 0.01, False)
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    m = get_metrics()
    assert m["multi.f"]["count"] == 50
