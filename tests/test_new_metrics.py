from tranq import get_metrics, reset_metrics
from tranq.metrics import record_metric


def test_percentiles_and_stats():
    reset_metrics()
    for i in range(1, 101):
        record_metric("perf", "fn", i / 100.0, False)
    m = get_metrics()["perf.fn"]
    assert m["count"] == 100
    assert m["errors"] == 0
    assert abs(m["min"] - 0.01) < 1e-9
    assert abs(m["max"] - 1.0) < 1e-9
    assert abs(m["avg"] - 0.505) < 1e-6
    assert 0.4 <= m["p50"] <= 0.6
    assert 0.9 <= m["p95"] <= 1.0
    assert 0.95 <= m["p99"] <= 1.0


def test_error_rate():
    reset_metrics()
    record_metric("e", "f", 0.1, False)
    record_metric("e", "f", 0.1, True)
    m = get_metrics()["e.f"]
    assert abs(m["error_rate"] - 0.5) < 1e-9


def test_backward_compat_keys():
    reset_metrics()
    record_metric("bc", "f", 0.5, False)
    m = get_metrics()["bc.f"]
    assert m["count"] == 1
    assert m["total_duration"] == 0.5
    assert m["errors"] == 0
