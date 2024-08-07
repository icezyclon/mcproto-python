import gc

import pytest

from mcproto._util import ThreadSafeSingeltonCache

# Note: set timeout for these tests, in case of deadlock we want to fail the test
# Should be at least 3 * SLEEP_TIME
TIMEOUT = 3

# Some tests use sleeps to simulate possible race conditions
# Define how long this should be - test precision is dependend on this!
SLEEP_TIME = 0.2


@pytest.mark.timeout(TIMEOUT)
def test_basic_use():
    class TestObject:
        def __init__(self, val) -> None:
            self.val = val

    cache = ThreadSafeSingeltonCache(TestObject)
    assert not cache.uses_weakref
    val = 1
    assert cache.get(val) is None
    o = cache.get_or_create(val)
    assert o
    assert isinstance(o, TestObject)
    assert o.val == val
    assert cache.get_or_create(val) is o
    assert cache.get(val) is o


@pytest.mark.timeout(TIMEOUT)
def test_basic_use_weakref():
    class TestObject:
        def __init__(self, val) -> None:
            self.val = val

    cache = ThreadSafeSingeltonCache(TestObject, use_weakref=True)
    assert cache.uses_weakref
    val = 1
    assert cache.get(val) is None
    o = cache.get_or_create(val)
    assert o
    assert isinstance(o, TestObject)
    assert o.val == val
    assert cache.get_or_create(val) is o
    assert cache.get(val) is o
    del o
    gc.collect()
    assert cache.get(val) is None
