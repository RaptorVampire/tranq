import sys
from pathlib import Path

# src-layout بدون نیاز به نصب: مسیر src را به sys.path اضافه می‌کنیم
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
