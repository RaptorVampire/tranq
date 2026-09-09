"""Example 35: Policy presets for common backends."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import presets

for name in ("http", "database", "redis", "kafka", "grpc", "llm"):
    cfg = getattr(presets, name)()
    print(f"{name:>9}: timeout={cfg.get('timeout')}, "
          f"wait={type(cfg['wait']).__name__}, stop={type(cfg['stop']).__name__}")

print()
print("HTTP preset retries on 429:")
class FakeHttpError(Exception):
    status_code = 429
cfg = presets.http()
print("   429 retryable?", cfg["retry_if"](FakeHttpError()))
