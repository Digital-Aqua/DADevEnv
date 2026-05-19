from typing import (
    Callable, Generic, Self, TypeVar, overload
)


_TClass = TypeVar('_TClass')
_T = TypeVar('_T')


class Prop(Generic[_TClass, _T]):
    """
    A quick and type-safe property descriptor.
    """
    def __init__(self,
        fget: Callable[[_TClass], _T],
        fset: Callable[[_TClass, _T], None]|None = None
    ):
        self._fget = fget
        self._fset = fset
        self.__doc__ = getattr(fget, '__doc__', None)

    @overload
    def __get__(self,
        obj: None,
        obj_type: type[_TClass]
    ) -> Self: ...
    @overload
    def __get__(self,
        obj: _TClass,
        obj_type: type[_TClass]
    ) -> _T: ...
    def __get__(self,
        obj: _TClass|None,
        obj_type: type[_TClass]
    ) -> _T|Self:
        if obj is None:
            return self
        return self._fget(obj)

    def __set__(self,
        obj: _TClass,
        value: _T
    ) -> None:
        if not self._fset:
            raise AttributeError("can't set attribute")
        self._fset(obj, value)

    def getter(self,
        fget: Callable[[_TClass], _T]
    ) -> 'Prop[_TClass, _T]':
        """
        Creates a new property with the new getter.
        """
        return prop(fget, self._fset)

    def setter(self,
        fset: Callable[[_TClass, _T], None]
    ) -> 'Prop[_TClass, _T]':
        """
        Creates a new property with the new setter.
        """
        return prop(self._fget, fset)

def prop(
    fget: Callable[[_TClass], _T],
    fset: Callable[[_TClass, _T], None]|None = None
) -> Prop[_TClass, _T]:
    """
    Creates a new property with the given getter and setter.
    """
    return Prop(fget, fset)
