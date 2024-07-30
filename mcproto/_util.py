import threading
import weakref
from typing import Callable, Hashable, TypeAlias, TypeVar


# Originally from: https://gist.github.com/Eboubaker/6a0b807788088a764b2a4c156fda0e4b
class ReentrantRWLock:
    """
    A lock object that allows many simultaneous "read locks", but only one "write lock."
    it also ignores multiple write locks from the same thread
    """

    def __init__(self) -> None:
        self._writer: int | None = None  # current writer
        self._readers: list[int] = []  # list of unique readers
        self._read_ready = threading.Condition(threading.Lock())
        # stack for 'with' keyword for write or read operations, 0 for read 1 for write
        self._with_ops_write: list[int] = []
        self._ops_arr_lock = threading.Lock()  # lock for previous list

    def acquire_read(self) -> None:
        """
        Acquire a read lock. Blocks only if a another thread has acquired the write lock.
        """
        ident: int = threading.current_thread().ident  # type: ignore
        if self._writer == ident or ident in self._readers:
            return
        with self._read_ready:
            self._readers.append(ident)

    def release_read(self) -> None:
        """
        Release a read lock if exists from this thread
        """
        ident: int = threading.current_thread().ident  # type: ignore
        if self._writer == ident or ident not in self._readers:
            return
        with self._read_ready:
            self._readers.remove(ident)
            if len(self._readers) == 0:
                self._read_ready.notify_all()

    def acquire_write(self) -> None:
        """
        Acquire a write lock. Blocks until there are no acquired read or write locks from another thread.
        """
        ident: int = threading.current_thread().ident  # type: ignore
        if self._writer == ident:
            return
        self._read_ready.acquire()
        me_included = 1 if ident in self._readers else 0
        while len(self._readers) - me_included > 0:
            self._read_ready.wait()
        self._writer = ident

    def release_write(self) -> None:
        """
        Release a write lock if exists from this thread.
        """
        if not self._writer or not self._writer == threading.current_thread().ident:
            return
        self._writer = None
        self._read_ready.release()

    def __enter__(self) -> None:
        with self._ops_arr_lock:
            if len(self._with_ops_write) == 0:
                raise RuntimeError(
                    "ReentrantRWLock: used 'with' block without call to for_read or for_write"
                )
            write = self._with_ops_write[-1]
        if write:
            self.acquire_write()
        else:
            self.acquire_read()

    def __exit__(self, exc_type, exc_value, tb) -> bool:
        with self._ops_arr_lock:
            write = self._with_ops_write.pop()
        if write:
            self.release_write()
        else:
            self.release_read()
        if exc_type is not None:
            return False  # exception happened
        return True

    def for_read(self) -> "ReentrantRWLock":
        """
        used for 'with' block
        """
        with self._ops_arr_lock:
            self._with_ops_write.append(0)
        return self

    def for_write(self) -> "ReentrantRWLock":
        """
        used for 'with' block
        """
        with self._ops_arr_lock:
            self._with_ops_write.append(1)
        return self


Key: TypeAlias = Hashable
Value = TypeVar("Value")


class ThreadSafeCachedKeyBasedFactory:
    def __init__(self, default_factory: Callable[[Key], Value], use_weakref: bool = False) -> None:
        self._default_factory = default_factory
        # lock must be reentrant, could deadlock otherwise (if constructing Impl in __init__ of Impl)
        self._lock = ReentrantRWLock()
        self._cache: dict[Key, Value] = weakref.WeakValueDictionary() if use_weakref else dict()

    @property
    def uses_weakref(self) -> bool:
        return isinstance(self._cache, weakref.WeakValueDictionary)

    def __getitem__(self, key: Key) -> Value:
        with self._lock.for_read():
            return self._cache[key]

    def __setitem__(self, key: Key, item: Value) -> None:
        with self._lock.for_write():
            self._cache[key] = item

    # Note: Deleting cannot happend explicitly, only via GC using weakref
    # Otherwise, we could not guarantee that the value is singleton
    # def __delitem__(self, key) -> None:
    #     with self._lock.for_write():
    #         del self._cache[key]

    # def clear(self) -> None:
    #     with self._lock.for_write():
    #         self._cache.clear()

    def get_or_create(self, key: Key, factory: Callable[[Key], Value] | None = None) -> Value:
        strong_ref = None
        with self._lock.for_read():
            try:
                strong_ref = self._cache[key]
            except KeyError:
                # might race between any check like "key in self._cache" so just try access instead
                # if self._cache is weakref (gc could run inbetween any two calls, therefore save strong reference in variable directly)
                pass
        # release read lock before aquiring write lock (could deadlock otherwise)
        if strong_ref is None:
            with self._lock.for_write():
                # must check again as entry could have been created while waiting for write lock (race condition)
                try:
                    strong_ref = self._cache[key]
                except KeyError:
                    pass
                if strong_ref is None:
                    # now we can be sure nobody will create entry with key because we have write lock
                    if factory is not None:
                        strong_ref = factory(key)
                    else:
                        strong_ref = self._default_factory(key)
                    self._cache[key] = strong_ref
        return strong_ref
