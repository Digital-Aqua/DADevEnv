from functools import lru_cache
from types import NoneType
from typing import (
    Iterable, TypeAliasType, TypeVar, overload
)

import jsonpath_ng as jp
from jsonpath_ng import JSONPath


__all__ = [
    'JNull', 'JBool', 'JNumber', 'JString',
    'JArray', 'JObject', 'JValue',
    'J',
    'JSONPath',
    'JValuePGColumn',
]


_T = TypeVar('_T')
_TJValue = TypeVar('_TJValue', bound='JValue')
_TJValue2 = TypeVar('_TJValue2', bound='JValue')


JNull = NoneType
""" A JSON null value. """
JBool = bool
""" A JSON boolean value. """
JNumber = float|int
""" A JSON number value. """
JString = str
""" A JSON string value. """
JValue = TypeAliasType(
    'JValue',
    'JNull | JBool | JNumber | JString | JArray | JObject',
)
""" A JSON value. """
JArray = list[JValue]
""" A JSON array value. """
JObject = dict[str, JValue]
""" A JSON object value. """


class _Raise: pass
_RAISE = _Raise()


def _check_jvalue(
    value: JValue,
    expected: type[_TJValue],
    default: _T|_Raise = _RAISE
) -> _TJValue|_T:
    """
        Checks if the value is of the expected type.
        If the value is of the expected type, returns it.

        If the value is not of the expected type,
        either raises a ValueError or returns the
        `default` parameter if provided.
    """
    if isinstance(value, expected):
        return value
    if isinstance(default, _Raise):
        raise ValueError(
            "Expected {%s}, got {%s}" % (
                expected.__name__,
                type(value).__name__
            )
        )
    return default


@lru_cache(maxsize=4096)
def _parse_jsonpath(path: str) -> JSONPath:
    return jp.parse(path)


class J():
    """
    Wraps one or more JSON values as a queriable selector.

    Example:
    ```python
    j = J([1, dict(a=2), [3, '4']])
    print(j('.[0]'))  # 1
    print(j('.[2][1]'))  # '4'
    ```
    """
    def __init__(self, *values: JValue):
        self._values = values
    
    def __call__(self, path: JSONPath|str) -> J:
        return J(*(
            result.value
            for value in self._values
            for result in _parse_jsonpath(path).find(value)
        ))

    def __iter__(self) -> Iterable[J]:
        return (J(value) for value in self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index: int) -> J:
        return J(self._values[index])

    def __contains__(self, value: JValue) -> bool:
        return value in self._values

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, J):
            return False
        return all(
            a == b
            for a, b in zip(
                self._values, other._values
            )
        )

    def values(self) -> Iterable[JValue]:
        """
        Yields the wrapped values.
        """
        yield from self._values

    @overload
    def nulls(self) -> Iterable[JNull]: ...
    @overload
    def nulls(self, default: _T) -> Iterable[JNull|_T]: ...
    def nulls(self,
        default: _T|_Raise = _RAISE
    ) -> Iterable[JNull|_T]:
        """
        Yields the wrapped null values.

        If a non-null value is found, returns `default`
        if provided, otherwise raises `ValueError`.
        """
        for value in self._values:
            yield _check_jvalue(value, NoneType, default)

    @overload
    def bools(self) -> Iterable[JBool]: ...
    @overload
    def bools(self, default: _T) -> Iterable[JBool|_T]: ...
    def bools(self,
        default: _T|_Raise = _RAISE
    ) -> Iterable[JBool|_T]:
        """
        Yields the wrapped boolean values.

        If a non-boolean value is found, returns `default`
        if provided, otherwise raises `ValueError`.
        """
        for value in self._values:
            yield _check_jvalue(value, bool, default)

    @overload
    def ints(self) -> Iterable[int]: ...
    @overload
    def ints(self, default: _T) -> Iterable[int|_T]: ...
    def ints(self,
        default: _T|_Raise = _RAISE
    ) -> Iterable[int|_T]:
        """
        Yields the wrapped integer values.

        If a non-integer value is found, returns `default`
        if provided, otherwise raises `ValueError`.
        """
        for value in self._values:
            yield _check_jvalue(value, int, default)

    @overload
    def floats(self) -> Iterable[float]: ...
    @overload
    def floats(self, default: _T) -> Iterable[float|_T]: ...
    def floats(self,
        default: _T|_Raise = _RAISE
    ) -> Iterable[float|_T]:
        """
        Yields the wrapped float values.

        If a non-float value is found, returns `default`
        if provided, otherwise raises `ValueError`.
        """
        for value in self._values:
            yield _check_jvalue(value, float, default)

    @overload
    def strs(self) -> Iterable[str]: ...
    @overload
    def strs(self, default: _T) -> Iterable[str|_T]: ...
    def strs(self,
        default: _T|_Raise = _RAISE
    ) -> Iterable[str|_T]:
        """
        Yields the wrapped string values.

        If a non-string value is found, returns `default`
        if provided, otherwise raises `ValueError`.
        """
        for value in self._values:
            yield _check_jvalue(value, str, default)

    @overload
    def arrs(self) -> Iterable[JArray]: ...
    @overload
    def arrs(self, default: _T) -> Iterable[JArray|_T]: ...
    def arrs(self,
        default: _T|_Raise = _RAISE
    ) -> Iterable[JArray|_T]:
        """
        Yields the wrapped array values.

        If a non-array value is found, returns `default`
        if provided, otherwise raises `ValueError`.
        """
        for value in self._values:
            yield _check_jvalue(value, list, default)

    @overload
    def objs(self) -> Iterable[JObject]: ...
    @overload
    def objs(self, default: _T) -> Iterable[JObject|_T]: ...
    def objs(self,
        default: _T|_Raise = _RAISE
    ) -> Iterable[JObject|_T]:
        """
        Yields the wrapped object values.

        If a non-object value is found, returns `default`
        if provided, otherwise raises `ValueError`.
        """
        for value in self._values:
            yield _check_jvalue(value, dict, default)

    @overload
    def value(self) -> JValue: ...
    @overload
    def value(self, default: _T) -> JValue|_T: ...
    def value(self,
        default: _T|_Raise = _RAISE
    ) -> JValue|_T:
        """
        Returns the single wrapped value.

        If there are no values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple values, always raises
        `ValueError`.
        """
        return self._value(default)
    def _value(self,
        default: _T|_Raise = _RAISE
    ) -> JValue|_T:
        if not self._values:
            if isinstance(default, _Raise):
                raise ValueError(
                    "Expected a single value, got none."
                )
            return default
        if len(self._values) != 1:
            raise ValueError(
                "Expected a single value, got multiple."
            )
        return self._values[0]

    @overload
    def null(self) -> JNull: ...
    @overload
    def null(self, default: _T) -> JNull|_T: ...
    def null(self, default: _T|_Raise = _RAISE) -> JNull|_T:
        """
        Returns the single wrapped null value.

        If there are no null values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple null values, always raises
        `ValueError`.
        """
        if not self._values \
            and not isinstance(default, _Raise):
               return default
        return _check_jvalue(self._value(), NoneType, default)

    @overload
    def bool(self) -> JBool: ...
    @overload
    def bool(self, default: _T) -> JBool|_T: ...
    def bool(self, default: _T|_Raise = _RAISE ) -> JBool|_T:
        """
        Returns the single wrapped boolean value.

        If there are no boolean values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple boolean values, always raises
        `ValueError`.
        """
        if not self._values \
            and not isinstance(default, _Raise):
               return default
        return _check_jvalue(self._value(), bool, default)
    
    @overload
    def int(self) -> int: ...
    @overload
    def int(self, default: _T) -> int|_T: ...
    def int(self, default: _T|_Raise = _RAISE) -> int|_T:
        """
        Returns the single wrapped integer value.

        If there are no integer values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple integer values, always raises
        `ValueError`.
        """
        if not self._values \
            and not isinstance(default, _Raise):
               return default
        value = self._value()
        if isinstance(value, float):
            return int(value)
        return _check_jvalue(value, int, default)
    
    @overload
    def float(self) -> float: ...
    @overload
    def float(self, default: _T) -> float|_T: ...
    def float(self, default: _T|_Raise = _RAISE) -> float|_T:
        """
        Returns the single wrapped float value.

        If there are no float values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple float values, always raises
        `ValueError`.
        """
        if not self._values \
            and not isinstance(default, _Raise):
               return default
        value = self._value()
        return _check_jvalue(value, float, default)
    
    @overload
    def str(self) -> JString: ...
    @overload
    def str(self, default: _T) -> JString|_T: ...
    def str(self, default: _T|_Raise = _RAISE) -> JString|_T:
        """
        Returns the single wrapped string value.

        If there are no string values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple string values, always raises
        `ValueError`.
        """
        if not self._values \
            and not isinstance(default, _Raise):
               return default
        return _check_jvalue(self._value(), str, default)
    
    @overload
    def arr(self) -> JArray: ...
    @overload
    def arr(self, default: _T) -> JArray|_T: ...
    def arr(self, default: _T|_Raise = _RAISE) -> JArray|_T:
        """
        Returns the single wrapped array value.

        If there are no array values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple array values, always raises
        `ValueError`.
        """
        if not self._values \
            and not isinstance(default, _Raise):
               return default
        return _check_jvalue(self._value(), list, default)

    @overload
    def obj(self) -> JObject: ...
    @overload
    def obj(self, default: _T) -> JObject|_T: ...
    def obj(self, default: _T|_Raise = _RAISE) -> JObject|_T:
        """
        Returns the single wrapped object value.

        If there are no object values, returns `default` if
        provided, otherwise raises `ValueError`.
        If there are multiple object values, always raises
        `ValueError`.
        """
        if not self._values \
            and not isinstance(default, _Raise):
               return default
        return _check_jvalue(self._value(), dict, default)


try:
    from sqlalchemy import Column
    from sqlalchemy.types import TypeEngine
    import sqlalchemy.dialects.postgresql as PG
except ImportError: pass
else:
    def JValuePGColumn(
        type_: type[TypeEngine[JValue]]|TypeEngine[JValue] \
            = PG.JSONB(),
        nullable: bool = False,
        **kwargs
    ) -> Column[JValue]:
        """
        A SQLAlchemy column for a JSON value.

        Keyword arguments are passed to SQLAlchemy's
        `Column` constructor.
        """
        return Column[JValue](
            type_ = type_,
            nullable = nullable,
            **kwargs
        )
