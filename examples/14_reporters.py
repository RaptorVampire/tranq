"""Example 14: Error reporting — FileReporter and custom reporters."""

import sys
import json
import tempfile
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

# 1. FileReporter — writes JSON lines
print("1) FileReporter:")
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
    log_path = tmp.name

try:
    file_reporter = tranq.FileReporter(log_path)

    @tranq.handle(on=ValueError, retry=0, reporters=[file_reporter])
    def failing_task():
        raise ValueError("something went wrong")

    try:
        failing_task()
    except ValueError:
        pass

    with open(log_path) as f:
        for line in f:
            record = json.loads(line)
            print(f"   Logged: {json.dumps(record, indent=2)}")
finally:
    os.unlink(log_path)

# 2. Custom reporter
print()
print("2) Custom reporter:")

class ConsoleReporter(tranq.Reporter):
    def __init__(self):
        self.reports = []

    def report(self, exception: BaseException, context: dict):
        msg = f"[ConsoleReporter] {type(exception).__name__}: {exception} in {context.get('func')}"
        print(f"   {msg}")
        self.reports.append((exception, context))

console_reporter = ConsoleReporter()

@tranq.handle(on=RuntimeError, retry=0, reporters=[console_reporter])
def another_failing():
    raise RuntimeError("another error")

try:
    another_failing()
except RuntimeError:
    pass

print(f"   Total reports collected: {len(console_reporter.reports)}")

# 3. Multiple reporters
print()
print("3) Multiple reporters at once:")
reports_a = []
reports_b = []

class ReporterA(tranq.Reporter):
    def report(self, e, ctx): reports_a.append(str(e))

class ReporterB(tranq.Reporter):
    def report(self, e, ctx): reports_b.append(str(e))

@tranq.handle(on=ValueError, retry=0, reporters=[ReporterA(), ReporterB()])
def multi_report():
    raise ValueError("broadcast me")

try:
    multi_report()
except ValueError:
    pass

print(f"   ReporterA got: {reports_a}")
print(f"   ReporterB got: {reports_b}")
