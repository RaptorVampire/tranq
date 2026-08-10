from collections import defaultdict
from threading import Lock

_metrics_lock = Lock()
_metrics = defaultdict(lambda: {"count": 0, "errors": 0, "total_duration": 0.0})

def record_metric(prefix: str, func_name: str, duration: float, is_error: bool):
    key = f"{prefix}.{func_name}" if prefix else func_name
    with _metrics_lock:
        m = _metrics[key]
        m["count"] += 1
        if is_error:
            m["errors"] += 1
        m["total_duration"] += duration

def get_metrics() -> dict:
    with _metrics_lock:
        return dict(_metrics)

def reset_metrics() -> None:
    with _metrics_lock:
        _metrics.clear()
