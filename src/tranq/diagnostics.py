"""Resilience diagnostics: health analysis and recommended actions."""
from .metrics import get_metrics
from .circuit_breaker import get_registry


def _classify(error_rate: float) -> str:
    if error_rate < 0.01:
        return "HEALTHY"
    if error_rate < 0.10:
        return "DEGRADED"
    return "UNHEALTHY"


def diagnostics() -> dict:
    """Build a full resilience diagnostics report.

    Returns a dict with per-service health, retry/timeout pressure, circuit
    states and a list of recommended actions.
    """
    metrics = get_metrics()
    services = {}
    total_calls = 0
    total_errors = 0

    for name, m in metrics.items():
        service = name.split(".")[0] if "." in name else name
        agg = services.setdefault(service, {"calls": 0, "errors": 0, "total_duration": 0.0})
        agg["calls"] += m["count"]
        agg["errors"] += m["errors"]
        agg["total_duration"] += m.get("total_duration", 0.0)
        total_calls += m["count"]
        total_errors += m["errors"]

    service_health = {}
    for service, agg in services.items():
        rate = (agg["errors"] / agg["calls"]) if agg["calls"] else 0.0
        service_health[service] = {
            "status": _classify(rate),
            "calls": agg["calls"],
            "errors": agg["errors"],
            "error_rate": rate,
        }

    # Circuit breaker states
    circuit_states = {}
    try:
        circuit_states = get_registry().states()
    except Exception:
        pass

    overall_rate = (total_errors / total_calls) if total_calls else 0.0

    # Recommended actions
    actions = []
    if overall_rate > 0.10:
        actions.append("Reduce retry count to lower retry pressure")
        actions.append("Enable fallbacks for critical paths")
    if overall_rate > 0.01:
        actions.append("Enable jitter to avoid thundering herds")
    if any(s == "open" for s in circuit_states.values()):
        actions.append("A circuit breaker is open; investigate the downstream service")
    if not actions:
        actions.append("System is healthy; no action required")

    return {
        "services": service_health,
        "overall": {
            "status": _classify(overall_rate),
            "calls": total_calls,
            "errors": total_errors,
            "error_rate": overall_rate,
        },
        "circuit_states": circuit_states,
        "recommended_actions": actions,
    }


def render_diagnostics() -> str:
    """Render a human-readable diagnostics report."""
    d = diagnostics()
    lines = ["SERVICE HEALTH", "-" * 40]
    for service, info in d["services"].items():
        lines.append(f"{service:<20} {info['status']}  "
                     f"(calls={info['calls']}, err_rate={info['error_rate']:.3f})")
    lines.append("")
    lines.append(f"Overall: {d['overall']['status']}  "
                 f"(calls={d['overall']['calls']}, errors={d['overall']['errors']})")
    if d["circuit_states"]:
        lines.append("")
        lines.append("CIRCUIT STATES")
        for name, state in d["circuit_states"].items():
            lines.append(f"  {name}: {state}")
    lines.append("")
    lines.append("Recommended actions:")
    for a in d["recommended_actions"]:
        lines.append(f"  - {a}")
    return "\n".join(lines)
