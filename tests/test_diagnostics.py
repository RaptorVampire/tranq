from tranq import reset_metrics, diagnostics, render_diagnostics
from tranq.metrics import record_metric


def test_diagnostics_healthy():
    reset_metrics()
    record_metric("api", "op", 0.1, False)
    d = diagnostics()
    assert d["overall"]["status"] == "HEALTHY"
    assert "api" in d["services"]


def test_diagnostics_unhealthy():
    reset_metrics()
    for _ in range(10):
        record_metric("svc", "op", 0.0, True)
    d = diagnostics()
    assert d["overall"]["status"] == "UNHEALTHY"
    assert len(d["recommended_actions"]) > 0


def test_render_diagnostics():
    reset_metrics()
    record_metric("api", "op", 0.1, False)
    out = render_diagnostics()
    assert "SERVICE HEALTH" in out
