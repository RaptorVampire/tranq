from .metrics import get_metrics


def summary_table(metrics: dict = None) -> str:
    """Render a human-readable metrics table."""
    data = metrics if metrics is not None else get_metrics()
    if not data:
        return "No metrics collected."

    headers = ["name", "calls", "errors", "err%", "total", "avg",
               "p50", "p95", "p99", "max"]
    rows = []
    for name, m in sorted(data.items()):
        rows.append([
            name,
            str(m["count"]),
            str(m["errors"]),
            f"{m['error_rate'] * 100:.1f}%",
            f"{m['total_duration']:.4f}s",
            f"{m['avg'] * 1000:.2f}ms",
            f"{m['p50'] * 1000:.2f}ms",
            f"{m['p95'] * 1000:.2f}ms",
            f"{m['p99'] * 1000:.2f}ms",
            f"{m['max'] * 1000:.2f}ms",
        ])

    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]

    def fmt(row):
        return " | ".join(c.ljust(w) for c, w in zip(row, widths))

    sep = "-+-".join("-" * w for w in widths)
    lines = [fmt(headers), sep] + [fmt(r) for r in rows]
    return "\n".join(lines)


def overall_health(metrics: dict = None) -> dict:
    """Aggregate health summary across all recorded metrics."""
    data = metrics if metrics is not None else get_metrics()
    total_calls = sum(m["count"] for m in data.values())
    total_errors = sum(m["errors"] for m in data.values())
    error_rate = (total_errors / total_calls) if total_calls else 0.0
    if error_rate < 0.01:
        status = "healthy"
    elif error_rate < 0.10:
        status = "degraded"
    else:
        status = "unhealthy"
    return {
        "total_calls": total_calls,
        "total_errors": total_errors,
        "error_rate": error_rate,
        "status": status,
    }


def render_report(metrics: dict = None) -> str:
    """Full textual report: health summary + metrics table."""
    health = overall_health(metrics)
    table = summary_table(metrics)
    header = (
        f"Status: {health['status']} | calls={health['total_calls']} "
        f"errors={health['total_errors']} error_rate={health['error_rate']:.4f}"
    )
    return f"{header}\n\n{table}"
