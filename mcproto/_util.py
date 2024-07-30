from __future__ import annotations

import contextlib
import threading
import weakref
from typing import Callable, Generator, Hashable, TypeAlias, TypeVar

__all__ = ["ReentrantRWLock", "ThreadSafeSingeltonCache"]


class ReentrantRWLock:
    """
    A lock object that allows many simultaneous "read locks", but only one "write lock."
    it also ignores multiple read/write locks from the same thread
    """

    def __init__(self) -> None:
        self._writer: int | None = None  # current writer
        self._readers: set[int] = set()  # set of readers
        self._lock = threading.Condition(threading.Lock())
        # _lock is used for:
        # * protecting write access to _writer and _readers
        # * is actively held by write lock (so no others can add themself to _readers)
        # * future writers can wait() on the lock to be notified once nobody is reading/writing anymore

    def acquire_read(self) -> None:
        """
        Acquire a read lock. Blocks only if a another thread has acquired the write lock.
        """
        ident: int = threading.current_thread().ident  # type: ignore
        if self._writer == ident or ident in self._readers:
            return
        with self._lock:
            self._readers.add(ident)

    def release_read(self) -> None:
        """
        Release a read lock if exists from this thread
        """
        ident: int = threading.current_thread().ident  # type: ignore
        if self._writer == ident or ident not in self._readers:
            return
        with self._lock:
            self._readers.remove(ident)
            if len(self._readers) == 0:
                self._lock.notify()  # last reader wakes the next writer if any

    def acquire_write(self) -> None:
        """
        Acquire a write lock. Blocks until there are no acquired read or write locks from another thread.
        """
        ident: int = threading.current_thread().ident  # type: ignore
        if self._writer == ident:
            return
        self._lock.acquire()
        is_reader = ident in self._readers
        self._readers.discard(ident)  # do not be reader while waiting for write or wake might fail
        while len(self._readers) > 0:
            self._lock.wait()
        self._writer = ident
        if is_reader:
            self._readers.add(ident)  # stay reader if was reader originally

    def release_write(self) -> None:
        """
        Release a write lock if exists from this thread.
        """
        if not self._writer or not self._writer == threading.current_thread().ident:
            return
        self._writer = None
        self._lock.notify()  # wake the next writer if any
        self._lock.release()

    @contextlib.contextmanager
    def for_read(self) -> Generator[ReentrantRWLock, None, None]:
        """
        used for 'with' block, e.g., with lock.for_read(): ...
        """
        try:
            self.acquire_read()
            yield self
        finally:
            self.release_read()

    @contextlib.contextmanager
    def for_write(self) -> Generator[ReentrantRWLock, None, None]:
        """
        used for 'with' block, e.g., with lock.for_write(): ...
        """
        try:
            self.acquire_write()
            yield self
        finally:
            self.release_write()


Key: TypeAlias = Hashable
Value = TypeVar("Value")


class ThreadSafeSingeltonCache:
    """This is a thread safe dictionary intended to be used as a cache.
    Using the get_or_create function guarantees that every object returned for a given key is a singleton across all threads.
    Objects that are not in the cache will be created using factory or otherwise default_factory initially.
    When useing use_weakref = True, then the values can be deleted by the Python garbage collector (GC) only if no other references,
    aside from this cache, exist to the object.
    Otherwise, with use_weakref = False, the keys are cached for the entire runtime of the program.

    Note, ideally only the get_or_create function should be used to fill the cache, as this function will
    create the objects initially and return them in a thread safe way.

    Note, preferably values should not be set directly or deleted, as that might violate the singleton invariant in some way.
    Only do that if you are sure what you are doing.
    """

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
        """Prefer using the get_or_create function for creating items."""
        with self._lock.for_write():
            self._cache[key] = item

    def __delitem__(self, key: Key) -> None:
        """Use with care! Once an object is deleted from the cache a new one might be created (might not be singleton anymore)"""
        with self._lock.for_write():
            del self._cache[key]

    def get(self, key: Key, default=None) -> Value | None:
        """Return the value for key if key is in the cache, else default.
        If default is not given, it defaults to None, so that this method never raises a KeyError.
        Does NOT create a new value in cache.
        Please do NOT check for the existance of an object to then set it without holding the write lock first!
        """
        try:
            return self[key]
        except KeyError:
            return default

    def get_or_create(self, key: Key, factory: Callable[[Key], Value] | None = None) -> Value:
        """Return singleton value for key or create value with factory (or otherwise default_factory) otherwise.
        Guarantees that a value with given key is a singleton in the entire program, even across multiple threads.
        """
        _sentinel = object()  # do not use None, as None could be a legit value in cache
        strong_ref = self.get(key, _sentinel)
        if strong_ref is _sentinel:
            with self._lock.for_write():
                # must check again as entry could have been created while waiting for write lock (race condition)
                strong_ref = self.get(key, _sentinel)
                if strong_ref is _sentinel:
                    # now we can be sure nobody will create entry with key because we have write lock
                    if factory is not None:
                        strong_ref = factory(key)
                    else:
                        strong_ref = self._default_factory(key)
                    self[key] = strong_ref
        return strong_ref
