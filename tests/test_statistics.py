from tranq import reset_metrics, summary_table, overall_health, render_report
from tranq.metrics import record_metric


def test_summary_table_empty():
    reset_metrics()
    assert summary_table() == "No metrics collected."


def test_summary_table_with_data():
    reset_metrics()
    record_metric("app", "op", 0.1, False)
    record_metric("app", "op", 0.2, True)
    table = summary_table()
    assert "app.op" in table
    assert "calls" in table


def test_overall_health():
    reset_metrics()
    record_metric("app", "ok", 0.1, False)
    h = overall_health()
    assert h["total_calls"] == 1
    assert h["total_errors"] == 0
    assert h["status"] == "healthy"


def test_overall_health_unhealthy():
    reset_metrics()
    for _ in range(10):
        record_metric("app", "bad", 0.0, True)
    h = overall_health()
    assert h["status"] == "unhealthy"


def test_render_report():
    reset_metrics()
    record_metric("app", "op", 0.05, False)
    rep = render_report()
    assert "Status" in rep
    assert "app.op" in rep
