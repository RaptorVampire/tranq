import pytest
from tranq import chaos, chaos_report, reset_chaos_reports


def test_chaos_latency():
    reset_chaos_reports()
    with chaos(latency=0.01) as inj:
        inj.maybe_inject()
    assert inj.counters["latency"] == 1


def test_chaos_error_injection():
    with chaos(error_rate=1.0, error_type=ValueError) as inj:
        with pytest.raises(ValueError):
            inj.maybe_inject()
    assert inj.counters["errors"] == 1


def test_chaos_report():
    reset_chaos_reports()
    with chaos(error_rate=1.0) as inj:
        try:
            inj.maybe_inject()
        except Exception:
            pass
    reports = chaos_report()
    assert len(reports) == 1
