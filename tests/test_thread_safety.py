import threading
from tranq import handle

def test_stateful_thread_isolation():
    errors = []
    def worker():
        counter = 0
        @handle(on=ValueError, retry=2, stateful=True, reraise=False)
        def f():
            nonlocal counter; counter += 1
            if counter < 3: raise ValueError("fail")
            return "ok"
        try:
            result = f()
            if result != "ok":
                errors.append(f"Expected 'ok', got {result}")
        except Exception as e:
            errors.append(str(e))
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(errors) == 0, f"Errors in threads: {errors}"
