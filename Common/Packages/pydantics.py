from base64 import b64decode, b64encode
from typing import (
    Annotated, Any, BinaryIO, Callable, Literal, Mapping,
    Self, TextIO
)
from uuid import UUID

from pydantic import (
    BaseModel, ConfigDict, Field, model_validator,
    BeforeValidator, PlainSerializer
)
from pydantic.config import ExtraValues
from pydantic.main import IncEx


__all__ = [
    'WithFrozen', 'Field', 'model_validator',
    'UUID_str', 'Bytes_b64',
    'YamlLoader',
]


_InfFloat = float


class WithModelDefaults(BaseModel):
    """
        Applies the usual defaults for a Pydantic model.
    """
    model_config = ConfigDict(
        use_attribute_docstrings=True
    )


class WithFrozen(BaseModel):
    """
        Freezes a Pydantic model.
    """
    model_config = ConfigDict(
        frozen=True
    )


try:
    import yaml
except ImportError: pass
else:
    YamlLoader = type[yaml.Loader] \
        | type[yaml.BaseLoader] \
        | type[yaml.FullLoader] \
        | type[yaml.SafeLoader] \
        | type[yaml.UnsafeLoader] \
        | type[yaml.CLoader] \
        | type[yaml.CBaseLoader] \
        | type[yaml.CFullLoader] \
        | type[yaml.CSafeLoader] \
        | type[yaml.CUnsafeLoader]

    class WithYaml(BaseModel):
        """
            Adds YAML serialization/deserialization to a
            Pydantic model.
        """
        def model_dump_yaml(self, *,
            include: IncEx | None = None,
            exclude: IncEx | None = None,
            context: Any | None = None,
            by_alias: bool | None = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            exclude_computed_fields: bool = False,
            round_trip: bool = False,
            warnings: bool | Literal[
                'none', 'warn', 'error'
            ] = True,
            fallback: Callable[[Any], Any] | None = None,
            serialize_as_any: bool = False,
            default_style: str | None = None,
            default_flow_style: bool | None = False,
            canonical: bool | None = None,
            indent: int | None = None,
            width: int | _InfFloat | None = None,
            allow_unicode: bool | None = None,
            line_break: str | None = None,
            encoding: None = None,
            explicit_start: bool | None = None,
            explicit_end: bool | None = None,
            version: tuple[int, int] | None = None,
            tags: Mapping[str, str] | None = None,
            sort_keys: bool = True
        ) -> str:
            """
                Generates a YAML representation of the
                model via PyYAML.

                See `yaml.dump` and `BaseModel.model_dump`
                for parameter details.
            """
            return yaml.dump(
                self.model_dump(
                    mode = 'json',
                    include = include,
                    exclude = exclude,
                    context = context,
                    by_alias = by_alias,
                    exclude_unset = exclude_unset,
                    exclude_defaults = exclude_defaults,
                    exclude_none = exclude_none,
                    exclude_computed_fields = \
                        exclude_computed_fields,
                    round_trip = round_trip,
                    warnings = warnings,
                    fallback = fallback,
                    serialize_as_any = serialize_as_any,
                ),
                default_style = default_style,
                default_flow_style = default_flow_style,
                canonical = canonical,
                indent = indent,
                width = width,
                allow_unicode = allow_unicode,
                line_break = line_break,
                encoding = encoding,
                explicit_start = explicit_start,
                explicit_end = explicit_end,
                version = version,
                tags = tags,
                sort_keys = sort_keys,
            )
        
        @classmethod
        def model_validate_yaml(cls,
            yaml_data: str | bytes | TextIO | BinaryIO, *,
            Loader: YamlLoader = yaml.SafeLoader,
            strict: bool | None = None,
            extra: ExtraValues | None = None,
            from_attributes: bool | None = None,
            context: Any | None = None,
            by_alias: bool | None = None,
            by_name: bool | None = None
        ) -> Self:
            return cls.model_validate(
                yaml.load(yaml_data, Loader=Loader),
                strict=strict,
                extra=extra,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name
            )


try:
    import sqlmodel
except ImportError: pass
else:
    Field = sqlmodel.Field

    class WithSql(sqlmodel.SQLModel):
        """
            Adds SQL support to a Pydantic model.
        """

        @classmethod
        def sqlmodel_col(cls, field: str | Any) -> Any:
            """
                Get the SQLAlchemy column for a
                SQLModel field.
            """
            if isinstance(field, str):
                return getattr(cls, field) \
                    .property.columns[0]
            else:
                return field.property.columns[0]

        @classmethod
        def sqlmodel_colname(cls, field: str | Any) -> str:
            """
                Get the qualified name of the column for a
                SQLMo`del field, as `<table>.<column>`.
            """
            try:
                col = cls.sqlmodel_col(field)
                col_name = col.name
                table_name = col.table.name
            except Exception:
                if isinstance(field, str):
                    col_name = field
                    table_name = getattr(
                        cls, '__tablename__', cls.__name__
                    )
                else:
                    raise
            return f"{table_name}.{col_name}"


def _uuid_from_str(v: UUID | str) -> UUID:
    if isinstance(v, UUID): return v
    return UUID(str(v))
UUID_str = Annotated[
    UUID,
    BeforeValidator(_uuid_from_str),
    PlainSerializer(str, when_used='json')
]
"""
    A `uuid.UUID` backed by a JSON string.
"""


def _bytes_from_b64(v: bytes | str) -> bytes:
    if isinstance(v, bytes): return v
    return b64decode(str(v).encode('ascii'))
def _bytes_to_b64(v: bytes) -> str:
    return b64encode(v).decode('ascii')
Bytes_b64 = Annotated[
    bytes,
    BeforeValidator(_bytes_from_b64),
    PlainSerializer(_bytes_to_b64, when_used='json'),
]
"""
    A `bytes` object backed by a base64 JSON string.
"""
