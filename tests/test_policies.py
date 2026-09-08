from tranq import Policy, set_global_policy, get_global_policy

def test_set_and_get_global():
    p = Policy(retry=5, delay=0.5)
    set_global_policy(p)
    assert get_global_policy().retry == 5
    assert get_global_policy().delay == 0.5
    set_global_policy(Policy())  # reset

def test_default_policy():
    set_global_policy(Policy())
    p = get_global_policy()
    assert p.retry == 0
    assert p.delay == 0.0
    assert p.backoff == 1.0
    assert p.reraise is True
