from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar
from weakref import WeakKeyDictionary

__all__ = [ 'wcache' ]


_T = TypeVar('_T')
_P = ParamSpec('_P')
_ArgsTuple = tuple[Any, ...]
_KwargsTuple = tuple[tuple[str, Any], ...]
_KeyTuple = tuple[_ArgsTuple, _KwargsTuple]
_InnerDict = dict[_KeyTuple, _T]


def wcache(func: Callable[_P, _T]) -> Callable[_P, _T]:
    """
    Caches the result of the decorated function weakly on its first argument.
    When the first argument is garbage collected, its associated results are
    also removed from the cache.
    """
    cache = WeakKeyDictionary[Any, _InnerDict[_T] ]()
    @wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        wkey = args[0]
        for i, a in enumerate(args):
            try:
                hash(a)
            except TypeError:
                raise TypeError(
                    f"Argument {i} of `{func.__name__}` must be hashable, "
                    f"got `{type(a).__name__}`."
                )
        for k, v in kwargs.items():
            try:
                hash(v)
            except TypeError:
                raise TypeError(
                    f"Keyword argument `{k}` of `{func.__name__}` must be "
                    f"hashable, got `{type(v).__name__}`."
                )
        key = (
            tuple(args),
            tuple(kwargs.items())
        )
        inner_cache = cache.setdefault(wkey, {})
        inner_cache.setdefault(key, func(*args, **kwargs))
        return inner_cache[key]
    return wrapper
