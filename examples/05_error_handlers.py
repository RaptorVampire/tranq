"""Example 05: Different callbacks for different exception types."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

def handle_value_error(e: ValueError):
    print(f"   [ValueError handler] {e}")

def handle_connection_error(e: ConnectionError):
    print(f"   [ConnectionError handler] {e}")

def handle_generic(e: Exception):
    print(f"   [Generic handler] {type(e).__name__}: {e}")

@tranq.handle(
    on=(ValueError, ConnectionError, KeyError),
    retry=0,
    reraise=False,
    on_error={
        ValueError: handle_value_error,
        ConnectionError: handle_connection_error,
        Exception: handle_generic,
    },
)
def risky_operation(kind: str):
    if kind == "value":
        raise ValueError("bad value")
    elif kind == "connection":
        raise ConnectionError("timeout")
    else:
        raise KeyError("missing")

print("1) ValueError:")
risky_operation("value")

print()
print("2) ConnectionError:")
risky_operation("connection")

print()
print("3) KeyError (falls back to generic handler):")
risky_operation("other")
