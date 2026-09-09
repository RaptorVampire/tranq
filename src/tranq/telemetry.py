"""OpenTelemetry integration (optional). Degrades gracefully when not installed."""
import functools
import inspect

try:
    from opentelemetry import trace as _otel_trace
    from opentelemetry import metrics as _otel_metrics
    OTEL_AVAILABLE = True
except ImportError:
    _otel_trace = None
    _otel_metrics = None
    OTEL_AVAILABLE = False


class Telemetry:
    """Emits spans and counters for resilience operations.

    If OpenTelemetry is not installed, all operations are no-ops so the rest
    of the library keeps working.
    """

    def __init__(self, service: str = "tranq"):
        self.service = service
        self.tracer = None
        self.counter = None
        if OTEL_AVAILABLE:
            self.tracer = _otel_trace.get_tracer(f"tranq.{service}")
            try:
                meter = _otel_metrics.get_meter(f"tranq.{service}")
                self.counter = meter.create_counter("tranq.events")
            except Exception:
                self.counter = None

    def span(self, name: str):
        if self.tracer is not None:
            return self.tracer.start_as_current_span(name)
        return _nullcontext()

    def event(self, name: str, **attributes):
        if self.counter is not None:
            try:
                attrs = {"service": self.service, "event": name}
                attrs.update({k: str(v) for k, v in attributes.items()})
                self.counter.add(1, attrs)
            except Exception:
                pass


class _nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


def telemetry(service: str = "tranq"):
    """Decorator attaching OpenTelemetry spans to a function."""
    telem = Telemetry(service)

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def aw(*args, **kwargs):
                with telem.span(func.__name__):
                    return await func(*args, **kwargs)
            return aw
        else:
            @functools.wraps(func)
            def w(*args, **kwargs):
                with telem.span(func.__name__):
                    return func(*args, **kwargs)
            return w
    return decorator
