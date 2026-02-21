from typing import Callable, TypeVar, runtime_checkable

_TProtocol = TypeVar('_TProtocol', bound=type)
_TType = TypeVar('_TType', bound=type)

_registered_implementations = set[tuple[type, type]]()

# def implements(
#     protocol: type[_TProtocol]
# ) -> Callable[[_TType], _TType]:
#     """
#     Decorator to register a class as an implementation
#     of a protocol.
#     """
#     def decorator(cls: _TType) -> _TType:
#         _registered_implementations.add((protocol, cls))
#         return runtime_checkable(cls)
#     return decorator

def implements(
    get_types: Callable[[], tuple[_TProtocol, type[_TProtocol]]]
) -> Callable[[_TType], _TType]:
    """
    Does nothing but trigger a linter error when the
    types returned by `get_types` do not match.
    """
    def decorator(cls: _TType) -> _TType:
        return cls
    return decorator


def assert_implements(
    protocol: type[_TProtocol],
    implementation: type[_TProtocol]
) -> _TProtocol: pass

def assert_implements2(
    protocol: _TProtocol,
) -> Callable[[_TProtocol], None]:
    def test(cls: _TProtocol) -> None:
        pass
    return test

# def test_implementations():
#     for protocol, cls in _registered_implementations:
#         assert issubclass(cls, protocol), ( \
#             f"Class {cls.__name__} does not implement "
#             f"protocol {protocol.__name__}."
#         )
