import math
from functools import lru_cache
from types import NoneType
from typing import Iterable, Literal, Self, TypeAliasType, TypeVar, cast, overload, override

import jsonpath_ng as jp
from jsonpath_ng import JSONPath


__all__ = [
    'JNull', 'JBool', 'JNumber', 'JString',
    'JArray', 'JObject', 'JValue',
    # 'jnull', 'jbool', 'jnumber', 'jstring',
    # 'jarray', 'jobject', 'jvalue',
    # 'jnulls', 'jbools', 'jnumbers', 'jstrings',
    # 'jarrays', 'jobjects',
    # 'jvalues', 'jvalue',
    'JSel',
    'JSONPath',
]


_T = TypeVar('_T')


JNull = NoneType
JBool = bool
JNumber = float|int
JString = str
JValue = TypeAliasType(
    'JValue',
    'JNull | JBool | JNumber | JString | JArray | JObject',
)
# JArray = TypeAliasType(
#     'JArray', 'list[JValue]'
# )
# JObject = TypeAliasType(
#     'JObject', 'dict[str, JValue]'
# )
JArray = list[JValue]
JObject = dict[str, JValue]


def _check_jvalue(
    value: JValue,
    expected: type[_TJValue]
) -> _TJValue:
    if not isinstance(value, expected):
        raise ValueError(
            "Expected {%s}, got {%s}" % (
                expected.__name__,
                type(value).__name__
            )
        )
    return value

# def _check_jvalue(
#     value: JValue,
#     *expected: type[JValue]
# ) -> JValue:
#     for e in expected:
#         if isinstance(value, e):
#             return value
#     raise ValueError(
#         "Expected {%s}, got {%s}" % (
#             "|".join(e.__name__ for e in expected),
#             type(value).__name__
#         )
#     )


@lru_cache(maxsize=4096)
def _parse_jsonpath(path: str) -> JSONPath:
    return jp.parse(path)

@overload
def _single(
    iterable: Iterable[_T],
    none_if_missing: Literal[True]
) -> _T|None:
    ...

@overload
def _single(
    iterable: Iterable[_T],
    none_if_missing: Literal[False]
) -> _T:
    ...

def _single(
    iterable: Iterable[_T],
    none_if_missing: bool = False
) -> _T|None:
    iterator = iter(iterable)
    try:
        result = next(iterator)
    except StopIteration:
        if none_if_missing:
            return None
        raise ValueError(
            "Expected a single value, got none."
        )
    try:
        next(iterator)
    except StopIteration:
        return result
    raise ValueError(
        "Expected a single value, got multiple."
    )


_TJValue = TypeVar('_TJValue', bound=JValue)


# @overload
# def jvalues(
#     value: JValue,
#     type_check: None,
#     path: JSONPath|str,
# ) -> Iterable[JValue]:
#     ...

# @overload
# def jvalues(
#     value: _TJValue,
#     type_check: type[_TJValue],
#     path: JSONPath|str,
# ) -> Iterable[_TJValue]:
#     ...

# @overload
# def jvalues(
#     value: _TJValue,
#     type_check: type[_TJValue]|None,
#     path: None = None,
# ) -> Iterable[_TJValue]:
#     ...

# def jvalues(
#     value: _TJValue|JValue,
#     type_check: type[_TJValue]|None = None,
#     path: JSONPath|str|None = None,
# ) -> Iterable[_TJValue|JValue]:
#     """ Gets JSON values at the given path. """
#     if not path:
#         yield value; return
#     if isinstance(path, str):
#         path = _parse_jsonpath(path)
#     for result in path.find(value):
#         value = result.value
#         if type_check:
#             value = _check_jvalue(result.value, type_check)
#         yield value


# @overload
# def jvalue(
#     value: JValue,
#     type_check: None,
#     path: JSONPath|str,
#     default: JValue
# ) -> JValue:
#     ...

# @overload
# def jvalue(
#     value: _TJValue,
#     type_check: type[_TJValue],
#     path: JSONPath|str,
#     default: _TJValue
# ) -> _TJValue:
#     ...

# @overload
# def jvalue(
#     value: _TJValue,
#     type_check: None,
#     path: None,
#     default: _TJValue
# ) -> _TJValue:
#     ...

# def jvalue(
#     value: _TJValue|JValue,
#     type_check: type[_TJValue]|None = None,
#     path: JSONPath|str|None = None,
#     default: _TJValue|JValue = None
# ) -> JValue|None:
#     """ Gets a single JSON value at the given path. """
#     if not path:
#         return value
#     i = iter(jvalues(value, type_check, path))
#     try:
#         result = next(i)
#     except StopIteration:
#         return default
#     try:
#         next(i)
#     except StopIteration:
#         return result
#     raise ValueError(
#         "Expected a single value, got multiple."
#     )


# def jnulls(
#     value: JValue,
#     path: JSONPath|str|None = None
# ) -> Iterable[JNull]:
#     """ Gets all JSON nulls at the given path. """
#     matches = jvalues(value, path)
#     for value in matches:
#         _check_jvalue(value, JNull)
#     yield from (
#         None
#         for _ in matches
#     )

# def jnull(
#     value: JValue,
#     path: JSONPath|str|None = None
# ) -> JNull:
#     """ Gets a single JSON null at the given path. """
#     return _single(jnulls(value, path), False)

# def jbools(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> Iterable[JBool]:
#     """ Gets all JSON booleans at the given path. """
#     matches = jvalues(value, path)
#     if coerce:
#         return (
#             bool(match)
#             for match in matches
#         )
#     return (
#         cast(bool, _check_jvalue(match, JBool))
#         for match in matches
#     )

# def jbool(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False,
#     none_if_missing: bool = False
# ) -> JBool|None:
#     """
#     Gets a single JSON boolean at the given path.
#     """
#     return _single(
#         jbools(value, path, coerce),
#         none_if_missing
#     )

# def jnumbers(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> Iterable[JNumber]:
#     """ Gets all JSON numbers at the given path. """
#     matches = jvalues(value, path)
#     if coerce:
#         return (
#             float(match) # type: ignore
#             for match in matches)
#     return (
#         cast(JNumber, _check_jvalue(match, float, int))
#         for match in matches
#     )

# def jnumber(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> JNumber:
#     """
#     Gets a single JSON number at the given path.
#     """
#     return _single(jnumbers(value, path, coerce))

# def jstrings(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> Iterable[JString]:
#     """ Gets all JSON strings at the given path. """
#     matches = jvalues(value, path)
#     if coerce:
#         return (
#             str(match)
#             for match in matches
#         )
#     return (
#         cast(JString, _check_jvalue(match, str))
#         for match in matches
#     )

# def jstring(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> JString:
#     """
#     Gets a single JSON string at the given path.
#     """
#     return _single(jstrings(value, path, coerce))

# def jarrays(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> Iterable[JArray]:
#     """ Gets all JSON arrays at the given path. """
#     matches = jvalues(value, path)
#     if coerce:
#         return (
#             list(match) # type: ignore
#             for match in matches
#         )
#     return (
#         cast(JArray, _check_jvalue(match, list))
#         for match in matches
#     )

# def jarray(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> JArray:
#     """
#     Gets a single JSON array at the given path.
#     """
#     return _single(jarrays(value, path, coerce))

# def jobjects(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> Iterable[JObject]:
#     """ Gets all JSON objects at the given path. """
#     matches = jvalues(value, path)
#     if coerce:
#         return (
#             dict[str, JValue](match) # type: ignore
#             for match in matches
#         )
#     return (
#         cast(JObject, _check_jvalue(match, dict))
#         for match in matches
#     )

# def jobject(
#     value: JValue,
#     path: JSONPath|str|None = None,
#     coerce: bool = False
# ) -> JObject:
#     """
#     Gets a single JSON objects at the given path.
#     """
#     return _single(jobjects(value, path, coerce))


class Raise: pass
RAISE = Raise()


class JSel():
    def __init__(self, *values: JValue):
        self._values = values
    
    def __call__(self, path: JSONPath|str) -> JSel:
        return JSel(*(
            result.value
            for value in self._values
            for result in _parse_jsonpath(path).find(value)
        ))

    def __iter__(self) -> Iterable[JSel]:
        return (JSel(value) for value in self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index: int) -> JSel:
        return JSel(self._values[index])

    def __contains__(self, value: JValue) -> bool:
        return value in self._values

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, JSel):
            return False
        return all(
            a == b
            for a, b in zip(
                self._values, other._values
            )
        )

    def values(self) -> Iterable[JValue]:
        yield from self._values

    def nulls(self) -> Iterable[JNull]:
        for value in self._values:
            yield _check_jvalue(value, NoneType)

    def bools(self) -> Iterable[bool]:
        for value in self._values:
            yield _check_jvalue(value, bool)

    def ints(self) -> Iterable[int]:
        for value in self._values:
            yield _check_jvalue(value, int)

    def floats(self) -> Iterable[float]:
        for value in self._values:
            yield _check_jvalue(value, float)

    def strs(self) -> Iterable[str]:
        for value in self._values:
            yield _check_jvalue(value, str)

    def arrs(self) -> Iterable[JArray]:
        for value in self._values:
            yield _check_jvalue(value, list)

    def objs(self) -> Iterable[JObject]:
        for value in self._values:
            yield _check_jvalue(value, dict)

    @overload
    def value(self) -> JValue: ...
    @overload
    def value(self, default: _T) -> JValue|_T: ...
    def value(self,
        default: _T|Raise = RAISE
    ) -> JValue|_T:
        return self._one(default)
    def _one(self,
        default: _T|Raise = RAISE
    ) -> JValue|_T:
        if not self._values:
            if isinstance(default, Raise):
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
    def null(self, default: _T|Raise = RAISE) -> JNull|_T:
        if not self._values \
            and not isinstance(default, Raise):
               return default
        return _check_jvalue(self._one(), NoneType)

    @overload
    def bool(self) -> JBool: ...
    @overload
    def bool(self, default: _T) -> JBool|_T: ...
    def bool(self, default: _T|Raise = RAISE ) -> JBool|_T:
        if not self._values \
            and not isinstance(default, Raise):
               return default
        return _check_jvalue(self._one(), bool)
    
    @overload
    def int(self) -> int: ...
    @overload
    def int(self, default: _T) -> int|_T: ...
    def int(self, default: _T|Raise = RAISE) -> int|_T:
        if not self._values \
            and not isinstance(default, Raise):
               return default
        value = self._one()
        if isinstance(value, float):
            return int(value)
        return _check_jvalue(value, int)
    
    @overload
    def float(self) -> float: ...
    @overload
    def float(self, default: _T) -> float|_T: ...
    def float(self, default: _T|Raise = RAISE) -> float|_T:
        if not self._values \
            and not isinstance(default, Raise):
               return default
        value = self._one()
        return _check_jvalue(value, float)
    
    @overload
    def str(self) -> JString: ...
    @overload
    def str(self, default: _T) -> JString|_T: ...
    def str(self, default: _T|Raise = RAISE) -> JString|_T:
        if not self._values \
            and not isinstance(default, Raise):
               return default
        return _check_jvalue(self._one(), str)
    
    @overload
    def arr(self) -> JArray: ...
    @overload
    def arr(self, default: _T) -> JArray|_T: ...
    def arr(self, default: _T|Raise = RAISE) -> JArray|_T:
        if not self._values \
            and not isinstance(default, Raise):
               return default
        return _check_jvalue(self._one(), list)

    @overload
    def obj(self) -> JObject: ...
    @overload
    def obj(self, default: _T) -> JObject|_T: ...
    def obj(self, default: _T|Raise = RAISE) -> JObject|_T:
        if not self._values \
            and not isinstance(default, Raise):
               return default
        return _check_jvalue(self._one(), dict)
