"""Dependency-aware resilience: track health of dependencies and react."""
import threading


class DependencyGraph:
    """Tracks the health of named dependencies and aggregates service health."""

    def __init__(self):
        self._deps = {}
        self._edges = {}
        self._lock = threading.Lock()

    def register(self, service: str, dependencies=None):
        with self._lock:
            self._deps.setdefault(service, {"calls": 0, "errors": 0})
            self._edges[service] = list(dependencies or [])
            for d in (dependencies or []):
                self._deps.setdefault(d, {"calls": 0, "errors": 0})

    def record(self, dependency: str, success: bool):
        with self._lock:
            d = self._deps.setdefault(dependency, {"calls": 0, "errors": 0})
            d["calls"] += 1
            if not success:
                d["errors"] += 1

    def health(self, dependency: str) -> str:
        with self._lock:
            d = self._deps.get(dependency)
            if not d or d["calls"] == 0:
                return "UNKNOWN"
            rate = d["errors"] / d["calls"]
            if rate < 0.01:
                return "HEALTHY"
            if rate < 0.10:
                return "DEGRADED"
            return "UNHEALTHY"

    def all_health(self) -> dict:
        with self._lock:
            names = list(self._deps.keys())
        return {name: self.health(name) for name in names}

    def failing_dependencies(self, service: str):
        with self._lock:
            deps = list(self._edges.get(service, []))
        return [d for d in deps if self.health(d) == "UNHEALTHY"]

    def render(self) -> str:
        lines = ["DEPENDENCY HEALTH", "-" * 40]
        for name, status in self.all_health().items():
            lines.append(f"{name:<20} {status}")
        return "\n".join(lines)
