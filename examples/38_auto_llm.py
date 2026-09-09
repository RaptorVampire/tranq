"""Example 38: tranq.auto() detection and LLM resilience."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import tranq
from tranq import recommend_policy, auto, llm

print("1) auto() policy detection:")
def fetch_users(): ...
def run_sql_query(): ...
def call_llm_completion(): ...

for fn in (fetch_users, run_sql_query, call_llm_completion):
    cfg = recommend_policy(fn)
    print(f"   {fn.__name__:<22} -> {cfg['detected_kind']}")

print()
print("2) @auto(verbose=True) recommendation (does not change behavior):")
@auto(verbose=True)
def fetch_orders():
    return "orders"
print("   result:", fetch_orders())

print()
print("3) LLM resilience with provider fallback:")
calls = {"primary": 0}

@llm(max_attempts=2, providers=[lambda *a, **k: "response-from-backup-provider"])
def ask_llm(prompt):
    calls["primary"] += 1
    raise ConnectionError("primary provider down")

print("   result:", ask_llm("hello"))
print("   primary attempts:", calls["primary"])
