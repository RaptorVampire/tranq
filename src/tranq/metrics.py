from collections import defaultdict, deque
from threading import Lock

_metrics_lock = Lock()
_metrics = defaultdict(lambda: {
    "count": 0,
    "errors": 0,
    "total_duration": 0.0,
    "min": float("inf"),
    "max": 0.0,
    "durations": deque(maxlen=1000),
})


def record_metric(prefix: str, func_name: str, duration: float, is_error: bool):
    key = f"{prefix}.{func_name}" if prefix else func_name
    with _metrics_lock:
        m = _metrics[key]
        m["count"] += 1
        if is_error:
            m["errors"] += 1
        m["total_duration"] += duration
        m["durations"].append(duration)
        if duration < m["min"]:
            m["min"] = duration
        if duration > m["max"]:
            m["max"] = duration


def _percentile(sorted_vals, p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def get_metrics(include_durations: bool = False) -> dict:
    """Return enriched metrics: count/errors/total/avg/min/max/error_rate + p50/p95/p99."""
    with _metrics_lock:
        out = {}
        for key, m in _metrics.items():
            durs = sorted(m["durations"])
            count = m["count"]
            entry = {
                "count": count,
                "errors": m["errors"],
                "total_duration": m["total_duration"],
                "min": 0.0 if not durs else m["min"],
                "max": m["max"],
                "avg": (m["total_duration"] / count) if count else 0.0,
                "error_rate": (m["errors"] / count) if count else 0.0,
                "p50": _percentile(durs, 0.50),
                "p95": _percentile(durs, 0.95),
                "p99": _percentile(durs, 0.99),
            }
            if include_durations:
                entry["durations"] = list(m["durations"])
            out[key] = entry
        return out


def reset_metrics() -> None:
    with _metrics_lock:
        _metrics.clear()
