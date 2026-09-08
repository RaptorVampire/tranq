import time
import asyncio
import pytest
from tranq import profile, async_profile, get_profile
import tranq.profiling as profiling_module

def test_sync_profile():
    profiling_module._profiles.clear()
    @profile
    def slow(): time.sleep(0.01); return "done"
    assert slow() == "done"
    s = get_profile("slow")
    assert s["calls"] == 1
    assert s["total_duration"] > 0

@pytest.mark.asyncio
async def test_async_profile():
    profiling_module._profiles.clear()
    @async_profile
    async def slow(): await asyncio.sleep(0.01); return "done"
    assert await slow() == "done"
    s = get_profile("slow")
    assert s["calls"] == 1
    assert s["total_duration"] > 0

def test_multiple_calls():
    profiling_module._profiles.clear()
    @profile
    def f(): pass
    for _ in range(5): f()
    assert get_profile("f")["calls"] == 5

def test_get_profile_no_args():
    profiling_module._profiles.clear()
    @profile
    def a(): pass
    @profile
    def b(): pass
    a(); b()
    all_p = get_profile()
    assert "a" in all_p and "b" in all_p
