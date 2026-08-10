import pytest
from tranq import mock_errors

def test_inject_with_probability_one():
    with pytest.raises(ValueError):
        with mock_errors(ValueError, probability=1.0):
            pass

def test_passthrough_real_exception():
    with pytest.raises(KeyError):
        with mock_errors(ValueError, probability=0.0):
            raise KeyError("real")

def test_seed_reproducible():
    with pytest.raises(ValueError):
        with mock_errors(ValueError, probability=0.99, seed=42):
            pass  # should always raise with seed 42
