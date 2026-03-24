from typing import (
    Callable, Generic, Iterable, Iterator, MutableSequence,
    TypeVar, overload
)


_TKey = TypeVar('_TKey')
_TValue = TypeVar('_TValue')

_SENTINEL = object()


class ListDict(Generic[_TKey, _TValue]):
    """ A mapping-like view of a list.

        Iteration yields values (list semantics), not keys. Key lookups use
        the selector to find the first matching item. With duplicate keys,
        __getitem__, __delitem__, and pop operate on the first occurrence.
    """

    def __init__(self,
        source: MutableSequence[_TValue],
        selector: Callable[[_TValue], _TKey],
    ):
        """ Creates a mapping-like view of a list.

            Args:
                source: The underlying mutable sequence. Mutations are shared.
                selector: Maps each value to its key for lookups.
        """
        self._selector = selector
        self._list = source

    def __getitem__(self, key: _TKey) -> _TValue:
        try:
            return next(
                item
                for item in self._list
                if self._selector(item) == key
            )
        except StopIteration:
            raise KeyError(f"Key {key} not found")

    def get(self, key: _TKey, default: _TValue | None = None) -> _TValue | None:
        """ Returns the first value for key, or default if not found.
        """
        try:
            return self[key]
        except KeyError:
            return default

    @overload
    def pop(self, key: _TKey) -> _TValue: ...

    @overload
    def pop(self, key: _TKey, default: _TValue) -> _TValue: ...

    def pop(self, key: _TKey, default: object = _SENTINEL) -> _TValue:
        """ Removes and returns the first value for key.
            Raises KeyError if key not found and no default given.
        """
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            if default is not _SENTINEL:
                return default  # type: ignore[return-value]
            raise

    def __repr__(self) -> str:
        keys_preview = list(self.keys())[:5]
        tail = ", ..." if len(self) > 5 else ""
        return f"ListDict(len={len(self)}, keys={keys_preview}{tail})"

    def __reversed__(self) -> Iterator[_TValue]:
        return reversed(self._list)

    def __setitem__(self, key: _TKey, value: _TValue) -> None:
        """ Updates the first match for key, or appends if key not found.
        """
        for i, item in enumerate(self._list):
            if self._selector(item) == key:
                self._list[i] = value
                return
        self._list.append(value)

    def setdefault(self, key: _TKey, default: _TValue) -> _TValue:
        """ Returns the first value for key, or sets and returns default.
        """
        try:
            return self[key]
        except KeyError:
            self._list.append(default)
            return default

    def index(self, key: _TKey) -> int:
        """ Returns the index of the first item whose selector output equals key.
            Raises KeyError if not found.
        """
        for i, item in enumerate(self._list):
            if self._selector(item) == key:
                return i
        raise KeyError(f"Key {key} not found")

    def append(self, value: _TValue) -> None:
        self._list.append(value)

    def extend(self, values: Iterable[_TValue]) -> None:
        self._list.extend(values)
    
    def __delitem__(self, key: _TKey) -> None:
        self._list.remove(self[key])
    
    def clear(self) -> None:
        self._list.clear()

    def __iter__(self) -> Iterator[_TValue]:
        return iter(self._list)

    def __len__(self) -> int:
        return len(self._list)

    def __contains__(self, key: _TKey|_TValue) -> bool:
        """ Membership test. True if key matches any selector output or any value.
        """
        return any(
            item == key or self._selector(item) == key
            for item in self._list
        )

    def keys(self) -> Iterable[_TKey]:
        """ Unique keys in list order (first occurrence wins).
        """
        return list(dict.fromkeys(
            self._selector(item)
            for item in self._list
        ))

    def values(self) -> Iterable[_TValue]:
        """ The underlying list (live reference). Mutations affect this ListDict.
        """
        return self._list

    def items(self) -> Iterable[tuple[_TKey, _TValue]]:
        """ Key-value pairs as a new list (snapshot).
        """
        return [
            (self._selector(item), item)
            for item in self._list
        ]
