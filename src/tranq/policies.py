from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Type


@dataclass
class Policy:
    """Encapsulates error-handling configuration."""
    retry: int = 0
    delay: float = 0.0
    backoff: float = 1.0
    backoff_strategy: str = "exponential"
    max_delay: Optional[float] = None
    jitter: bool = False
    reraise: bool = True
    log_level: int = 40
    log_format: Optional[str] = None
    retry_if: Optional[Callable[[BaseException], bool]] = None
    retry_on_result: Optional[Callable[[Any], bool]] = None
    on_error: Optional[Dict[Type[BaseException], Callable]] = None
    metrics: bool = False
    metric_prefix: str = ""
    circuit_breaker: Optional[object] = None
    stateful: bool = False
    reporters: List[object] = field(default_factory=list)
    priority: int = 0
    inject: Dict[str, Any] = field(default_factory=dict)
    # --- professional fields (v1.0.0) ---
    timeout: Optional[float] = None
    on_retry: Optional[Callable] = None
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    retry_budget: Optional[object] = None


_DEFAULT_POLICY = Policy()
_policy_lock = Lock()


def set_global_policy(policy: Policy) -> None:
    global _DEFAULT_POLICY
    with _policy_lock:
        _DEFAULT_POLICY = policy


def get_global_policy() -> Policy:
    with _policy_lock:
        return _DEFAULT_POLICY
