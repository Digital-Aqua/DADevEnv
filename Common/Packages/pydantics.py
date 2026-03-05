from base64 import b64decode, b64encode
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel, ConfigDict, Field, model_validator,
    BeforeValidator, PlainSerializer
)

__all__ = [
    'FrozenBaseModel', 'Field', 'model_validator',
    'UUID_str', 'Bytes_b64'
]


class FrozenBaseModel(BaseModel):
    """
    A base model that is frozen and supports
    attribute docstrings.
    """
    model_config = ConfigDict(
        frozen=True,
        use_attribute_docstrings=True,
    )


def _uuid_from_str(v: UUID | str) -> UUID:
    if isinstance(v, UUID): return v
    return UUID(str(v))
UUID_str = Annotated[
    UUID,
    BeforeValidator(_uuid_from_str),
    PlainSerializer(str),
]
"""
A UUID backed by a string in pydantic.
"""


def _bytes_from_b64(v: bytes | str) -> bytes:
    if isinstance(v, bytes): return v
    return b64decode(str(v).encode('ascii'))
def _bytes_to_b64(v: bytes) -> str:
    return b64encode(v).decode('ascii')
Bytes_b64 = Annotated[
    bytes,
    BeforeValidator(_bytes_from_b64),
    PlainSerializer(_bytes_to_b64),
]
"""
A bytes object backed by a base64 string in pydantic.
"""
