"""Run all example scripts sequentially."""

import subprocess
import sys
from pathlib import Path

examples_dir = Path(__file__).resolve().parent
scripts = sorted(examples_dir.glob("[0-9][0-9]_*.py"))

if not scripts:
    print("No example scripts found.")
    sys.exit(1)

failed = []
for script in scripts:
    print()
    print("=" * 60)
    print(f"Running {script.name}")
    print("=" * 60)
    result = subprocess.run([sys.executable, str(script)], cwd=examples_dir)
    if result.returncode != 0:
        failed.append(script.name)

print()
print("=" * 60)
if failed:
    print(f"FAILED: {len(failed)} script(s): {', '.join(failed)}")
    sys.exit(1)
else:
    print(f"All {len(scripts)} examples ran successfully.")
