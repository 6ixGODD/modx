from __future__ import annotations

import abc
import typing as t

from modx.helpers.mixin import LoggingTagMixin


class Empty:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<EMPTY>"

    __str__ = __repr__

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, Empty)

    def __hash__(self) -> int:
        return hash("<EMPTY>")


EMPTY = Empty()


class Placeholder:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<PLACEHOLDER>"

    __str__ = __repr__

    def __bool__(self) -> bool:
        return True

    def __getstate__(self):
        return ()

    def __setstate__(self, state: tuple):
        pass

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, Placeholder)

    def __hash__(self) -> int:
        return hash("<PLACEHOLDER>")


PLACEHOLDER = Placeholder()


class CacheMiss:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<CACHE_MISS>"

    __str__ = __repr__

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, CacheMiss)

    def __hash__(self) -> int:
        return hash("<CACHE_MISS>")

    def __getstate__(self):
        return ()

    def __setstate__(self, state: tuple):
        pass


CACHE_MISS = CacheMiss()

V = t.TypeVar('V')


class KVCache(t.MutableMapping[str, V], LoggingTagMixin):
    @abc.abstractmethod
    def __getitem__(self, key: str) -> V | Empty:
        """Retrieve an item from the cache by key."""
        pass

    @abc.abstractmethod
    def __setitem__(self, key: str, value: V) -> None:
        """Set an item in the cache with the specified key and value."""
        pass

    @abc.abstractmethod
    def __delitem__(self, key: str) -> None:
        """Delete an item from the cache by key."""
        pass

    @abc.abstractmethod
    def __iter__(self) -> t.Iterator[str]:
        """Return an iterator over the keys in the cache."""
        pass

    @abc.abstractmethod
    def __len__(self) -> int:
        """Return the number of items in the cache."""
        pass

    @abc.abstractmethod
    def __contains__(self, key: object, /) -> bool:
        """Check if the cache contains a specific key."""
        pass

    @abc.abstractmethod
    def get(self, key: str, /):
        """Get an item from the cache, returning None if the key does not
        exist."""
        pass

    @abc.abstractmethod
    def setdefault(self, key: str, default: V | None = None, /) -> V:
        """Set a default value for a key if it does not exist in the cache."""
        pass

    @abc.abstractmethod
    def clear(self) -> None:
        """Clear all items from the cache."""
        pass

    @abc.abstractmethod
    def pop(self, key: str, /) -> V | Empty:
        """Remove and return an item from the cache by key."""
        pass

    @abc.abstractmethod
    def popitem(self) -> t.Tuple[str, V] | Empty:
        """Remove and return an arbitrary (key, value) pair from the cache."""
        pass

    @abc.abstractmethod
    def set(self, key: str, value: V, /) -> None:
        """Set an item in the cache with the specified key and value."""
        pass

    @abc.abstractmethod
    def setx(
        self,
        key: str,
        value: V, /,
        ttl: int | None = None
    ) -> None:
        """Set an item in the cache with the specified key, value, and
        optional time-to-live (TTL)."""
        pass

    @abc.abstractmethod
    def ttl(self, key: str, /) -> int | None:
        """Get the time-to-live (TTL) for a specific key in the cache."""
        pass

    @abc.abstractmethod
    def expire(self, key: str, /, ttl: int | None = None) -> None:
        """Set the time-to-live (TTL) for a specific key in the cache."""
        pass

    @abc.abstractmethod
    def incr(self, key: str, /, amount: int = 1) -> int:
        """Increment the integer value of a key by the given amount. If the key
        does not exist, it is set to 0 before performing the operation."""
        pass

    @abc.abstractmethod
    def decr(self, key: str, /, amount: int = 1) -> int:
        """Decrement the integer value of a key by the given amount. If the key
        does not exist, it is set to 0 before performing the operation."""
        pass
