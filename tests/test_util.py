import time
from threading import Thread

import pytest

from mcproto._util import ReentrantRWLock

# Note: set timeout for these tests, in case of deadlock we want to fail the test
# Should be at least 3 * SLEEP_TIME
TIMEOUT = 5

# Some tests use sleeps to simulate possible race conditions
# Define how long this should be - test precision is dependend on this!
SLEEP_TIME = 0.5


@pytest.mark.timeout(TIMEOUT)
def test_single_threaded_upgrade():
    lock = ReentrantRWLock()

    with lock.for_read():
        with lock.for_write():
            pass


@pytest.mark.timeout(TIMEOUT)
def test_single_threaded_reentrant_read():
    lock = ReentrantRWLock()

    with lock.for_read():
        with lock.for_read():
            pass


@pytest.mark.timeout(TIMEOUT)
def test_single_threaded_reentrant_write():
    lock = ReentrantRWLock()

    with lock.for_write():
        with lock.for_write():
            pass


@pytest.mark.timeout(TIMEOUT)
def test_single_threaded_read_when_write():
    lock = ReentrantRWLock()

    with lock.for_write():
        with lock.for_read():
            pass


@pytest.mark.timeout(TIMEOUT)
def test_single_threaded_deep():
    lock = ReentrantRWLock()

    with lock.for_read():
        with lock.for_read():
            with lock.for_write():
                with lock.for_read():
                    with lock.for_write():
                        pass


@pytest.mark.timeout(TIMEOUT)
def test_lock_no_ambiguous_context():
    lock = ReentrantRWLock()

    with pytest.raises(AttributeError):
        with lock:
            pass


@pytest.mark.timeout(TIMEOUT)
def test_multi_threaded_many_reads():
    lock = ReentrantRWLock()

    def read():
        with lock.for_read():
            time.sleep(SLEEP_TIME)
            return

    t1 = Thread(name="read1", target=read, daemon=True)
    t2 = Thread(name="read2", target=read, daemon=True)
    start = time.perf_counter()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    end = time.perf_counter()
    # a bit more than SLEEP_TIME, definitly less than 2 * SLEEP_TIME!
    assert (
        end - start < SLEEP_TIME * 1.5
    ), f"Time for both joins was {end - start}, should be < {SLEEP_TIME * 1.5}"


@pytest.mark.timeout(TIMEOUT)
def test_multi_threaded_write_exclusive():
    lock = ReentrantRWLock()

    def write():
        with lock.for_write():
            time.sleep(SLEEP_TIME)
            return

    t1 = Thread(name="write1", target=write, daemon=True)
    t2 = Thread(name="write2", target=write, daemon=True)
    start = time.perf_counter()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    end = time.perf_counter()
    # definitly at least 2 * SLEEP_TIME!
    assert (
        end - start > 1.9 * SLEEP_TIME
    ), f"Time for both joins was {end - start}, should be > {1.9 * SLEEP_TIME}"


@pytest.mark.timeout(TIMEOUT)
def test_multi_threaded_read_write_exclusive():
    lock = ReentrantRWLock()

    def read():
        print("Before read aquire")
        with lock.for_read():
            print("Before read sleep")
            time.sleep(SLEEP_TIME)
            print("read done")
            return

    def write():
        print("Before write aquire")
        with lock.for_write():
            print("Before write sleep")
            time.sleep(SLEEP_TIME)
            print("write done")
            return

    t1 = Thread(name="read", target=read, daemon=True)
    t2 = Thread(name="write", target=write, daemon=True)
    start = time.perf_counter()
    t1.start()
    time.sleep(0.01)
    t2.start()
    t1.join()
    t2.join()
    end = time.perf_counter()
    # definitly at least 2 * SLEEP_TIME!
    assert (
        end - start > 1.9 * SLEEP_TIME
    ), f"Time for both joins was {end - start}, should be > {1.9 * SLEEP_TIME}"


@pytest.mark.timeout(TIMEOUT)
def test_multi_threaded_write_read_exclusive():
    lock = ReentrantRWLock()

    def read():
        print("Before read aquire")
        with lock.for_read():
            print("Before read sleep")
            time.sleep(SLEEP_TIME)
            print("read done")
            return

    def write():
        print("Before write aquire")
        with lock.for_write():
            print("Before write sleep")
            time.sleep(SLEEP_TIME)
            print("write done")
            return

    t1 = Thread(name="write", target=write, daemon=True)
    t2 = Thread(name="read", target=read, daemon=True)
    start = time.perf_counter()
    t1.start()
    time.sleep(0.01)
    t2.start()
    t1.join()
    t2.join()
    end = time.perf_counter()
    # definitly at least 2 * SLEEP_TIME!
    assert (
        end - start > 1.9 * SLEEP_TIME
    ), f"Time for both joins was {end - start}, should be > {1.9 * SLEEP_TIME}"


@pytest.mark.timeout(TIMEOUT)
def test_multi_threaded_read_write_exclusive_direct():
    lock = ReentrantRWLock()

    def read():
        print("Before read aquire")
        lock.acquire_read()
        print("Before read sleep")
        time.sleep(SLEEP_TIME)
        print("read done")
        lock.release_read()

    def write():
        print("Before write aquire")
        lock.acquire_write()
        print("Before write sleep")
        time.sleep(SLEEP_TIME)
        print("write done")
        lock.release_write()

    t1 = Thread(name="read", target=read, daemon=True)
    t2 = Thread(name="write", target=write, daemon=True)
    start = time.perf_counter()
    t1.start()
    time.sleep(0.01)
    t2.start()
    t1.join()
    t2.join()
    end = time.perf_counter()
    # definitly at least 2 * SLEEP_TIME!
    assert (
        end - start > 1.9 * SLEEP_TIME
    ), f"Time for both joins was {end - start}, should be > {1.9 * SLEEP_TIME}"


@pytest.mark.timeout(TIMEOUT)
def test_multi_threaded_write_read_exclusive_direct():
    lock = ReentrantRWLock()

    def read():
        print("Before read aquire")
        lock.acquire_read()
        print("Before read sleep")
        time.sleep(SLEEP_TIME)
        print("read done")
        lock.release_read()

    def write():
        print("Before write aquire")
        lock.acquire_write()
        print("Before write sleep")
        time.sleep(SLEEP_TIME)
        print("write done")
        lock.release_write()

    t1 = Thread(name="write", target=write, daemon=True)
    t2 = Thread(name="read", target=read, daemon=True)
    start = time.perf_counter()
    t1.start()
    time.sleep(0.01)
    t2.start()
    t1.join()
    t2.join()
    end = time.perf_counter()
    # definitly at least 2 * SLEEP_TIME!
    assert (
        end - start > 1.9 * SLEEP_TIME
    ), f"Time for both joins was {end - start}, should be > {1.9 * SLEEP_TIME}"
