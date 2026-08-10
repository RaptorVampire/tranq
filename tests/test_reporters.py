import json
import os
import tempfile
from tranq import FileReporter

def test_file_reporter_writes_json():
    with tempfile.NamedTemporaryFile(mode="r+", delete=False, suffix=".json") as f:
        path = f.name
    try:
        rep = FileReporter(path)
        rep.report(ValueError("test error"), {"func": "myfunc", "attempt": 2})
        with open(path) as f:
            data = json.loads(f.readline())
        assert data["exception_type"] == "ValueError"
        assert data["exception_message"] == "test error"
        assert data["function"] == "myfunc"
        assert data["attempt"] == 2
        assert "timestamp" in data
    finally:
        os.unlink(path)

def test_file_reporter_creates_directory():
    import tempfile, shutil
    d = tempfile.mkdtemp()
    subdir = os.path.join(d, "logs", "sub")
    path = os.path.join(subdir, "errors.json")
    try:
        rep = FileReporter(path)
        rep.report(ValueError("x"), {"func": "f"})
        assert os.path.exists(path)
    finally:
        shutil.rmtree(d)
