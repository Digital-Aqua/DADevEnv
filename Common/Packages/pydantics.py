from base64 import b64decode, b64encode
from typing import (
    Annotated, Any, Awaitable, BinaryIO, Callable, Literal,
    Mapping, Self, Sequence, TextIO, overload
)
from uuid import UUID

from pydantic import (
    BaseModel, ConfigDict, Field, model_validator,
    BeforeValidator, PlainSerializer
)
from pydantic.config import ExtraValues
from pydantic.main import IncEx


__all__ = [
    'Field', 'Column', 'model_validator',
    'WithModelDefaults', 'WithFrozen',
    'WithYaml', 'WithJObject', 'WithSql',
    'UUID_str', 'UUIDPGColumn', 'UUIDSeqPGColumn',
    'Bytes_b64', 'BytesPGColumn',
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
    from .jsontypes import JObject
except ImportError: pass
else:
    class WithJObject(BaseModel):
        """ Adds JObject support to a Pydantic model. """
        def model_dump_jobject(self) -> JObject:
            """ Dumps the model as a JObject. """
            return self.model_dump(mode='json')


try:
    import sqlmodel
    from sqlmodel import Session
    from sqlmodel.ext.asyncio.session import AsyncSession
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
                Gets the SQLAlchemy column for a
                SQLModel field.
            """
            if isinstance(field, str):
                return cls.__table__.c[field] # type: ignore[attr-defined]
            # InstrumentedAttribute has .key and .class_
            if hasattr(field, 'key') and hasattr(field, 'class_'):
                return field.class_.__table__.c[field.key]
            # Column has .name and optionally .table
            if hasattr(field, 'name'):
                return field
            # Legacy: InstrumentedAttribute with .property
            if hasattr(field, 'property'):
                return field.property.columns[0]
            raise AttributeError(
                f"Cannot get column from {field!r}"
            )

        @classmethod
        def sqlmodel_colname(cls, field: str | Any) -> str:
            """
                Gets the qualified name of the column for a
                SQLModel field, as `<table>.<column>`.
            """
            try:
                col = cls.sqlmodel_col(field)
                col_name = col.name
                table_name = (
                    col.table.name
                    if col.table is not None
                    else (
                        getattr(field, 'class_', cls).__tablename__
                        if not isinstance(field, str)
                        else getattr(cls, '__tablename__', cls.__name__)
                    )
                )
                if table_name is None:
                    table_name = getattr(
                        getattr(field, 'class_', cls), '__name__', 'table'
                    ).lower()
            except Exception:
                if isinstance(field, str):
                    col_name = field
                    table_name = getattr(
                        cls, '__tablename__', cls.__name__
                    )
                else:
                    raise
            return f"{table_name}.{col_name}"
    
        @overload
        def sqlmodel_add(self,
            session: Session
        ) -> None: ...
        @overload
        def sqlmodel_add(self,
            session: AsyncSession
        ) -> Awaitable[None]: ...
        def sqlmodel_add(self,
            session: Session|AsyncSession
        ) -> None|Awaitable[None]:
            """ Adds this model to the session and commits.
            """
            session.add(self)
            return session.commit()


def _uuid_from_str(v: UUID | str) -> UUID:
    if isinstance(v, UUID): return v
    return UUID(str(v))
UUID_str = Annotated[
    UUID,
    BeforeValidator(_uuid_from_str),
    PlainSerializer(str, when_used='json')
]
""" A `uuid.UUID` backed by a JSON string. """

try:
    from sqlalchemy import Column
    from sqlalchemy.types import TypeEngine
    import sqlalchemy.dialects.postgresql as PG
except ImportError: pass
else:
    def UUIDPGColumn(
        type_: type[TypeEngine[UUID]]|TypeEngine[UUID] \
            = PG.UUID(),
        nullable: bool = False,
        **kwargs
    ) -> Column[UUID]:
        """
            A SQLAlchemy column for a `UUID` object.

            Keyword arguments are passed to SQLAlchemy's
            `Column` constructor.
        """
        return Column[UUID](
            type_ = type_,
            nullable = nullable,
            **kwargs
        )

    def UUIDSeqPGColumn(
        type_: type[TypeEngine[Sequence[UUID]]]|TypeEngine[Sequence[UUID]] \
            = PG.ARRAY(
                PG.UUID(),
                dimensions = 1,
                zero_indexes = False
            ),
        nullable: bool = True,
        **kwargs: Any
    ) -> Column[Sequence[UUID]]:
        """
            A SQLAlchemy column for a sequence of `UUID`
            objects.

            Keyword arguments are passed to SQLAlchemy's
            `Column` constructor.
        """
        return Column[Sequence[UUID]](
            type_ = type_,
            nullable = nullable,
            **kwargs
        )


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
""" A `bytes` object backed by a base64 JSON string. """

try:
    from sqlalchemy import Column
    from sqlalchemy.types import TypeEngine
    import sqlalchemy.dialects.postgresql as PG
except ImportError: pass
else:
    def BytesPGColumn(
        type_: type[TypeEngine[bytes]]|TypeEngine[bytes] \
            = PG.BYTEA(),
        nullable: bool = False,
        **kwargs
    ) -> Column[bytes]:
        """
            A SQLAlchemy column for a `bytes` object.

            Keyword arguments are passed to SQLAlchemy's
            `Column` constructor.
        """
        return Column[bytes](
            type_ = type_,
            nullable = nullable,
            **kwargs
        )
