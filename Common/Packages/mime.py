from dataclasses import dataclass, asdict
from typing import Annotated, Self

from mimeparse import parse_mime_type


__all__ = [
    'MimeType',
    'MimeType_str',
    'MIME_BINARY',
    'MIME_PLAINTEXT_UTF8',
    'MIME_PLAINTEXT',
    'MIME_JSON',
    'MIME_YAML',
    'MIME_MARKDOWN',
]


@dataclass(frozen=True)
class MimeType:
    main_type: str
    sub_type: str
    parameters: dict[str, str]

    @classmethod
    def parse(cls, mime_type: str|MimeType) -> Self:
        """
        Parse a MIME type string or object into a
        `MimeType` object.
        """
        if isinstance(mime_type, MimeType):
            return cls(**asdict(mime_type))
        return cls(*parse_mime_type(mime_type))
    
    def __str__(self) -> str:
        if not self.parameters:
            return self.mainsubtype
        param_part = "; ".join(
            f"{k}={v}"
            for k, v in self.parameters.items()
        )
        return f'{self.mainsubtype}; {param_part}'

    @property
    def mainsubtype(self) -> str:
        return f'{self.main_type}/{self.sub_type}'

    @property
    def charset(self) -> str|None:
        """
        Get the charset parameter of the MIME type, if any.
        """
        return self.parameters.get('charset')

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            try:
                other = MimeType.parse(other)
            except Exception:
                return NotImplemented
        if not isinstance(other, MimeType):
            return NotImplemented
        return (
            self.main_type.lower() == other.main_type.lower() and
            self.sub_type.lower() == other.sub_type.lower() and
            {k.lower(): v for k, v in self.parameters.items()} == 
            {k.lower(): v for k, v in other.parameters.items()}
        )

    def __hash__(self) -> int:
        return hash((
            self.main_type.lower(),
            self.sub_type.lower(),
            frozenset((k.lower(), v) for k, v in self.parameters.items())
        ))

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            try:
                item = MimeType.parse(item)
            except Exception:
                return False
        if not isinstance(item, MimeType):
            return False
            
        if self.main_type != '*' and self.main_type.lower() != item.main_type.lower():
            return False
        if self.sub_type != '*' and self.sub_type.lower() != item.sub_type.lower():
            return False
            
        self_params = {k.lower(): v for k, v in self.parameters.items()}
        item_params = {k.lower(): v for k, v in item.parameters.items()}
        
        for k, v in self_params.items():
            if k not in item_params or item_params[k] != v:
                return False
                
        return True

    def copy(self,
        main_type: str | None = None,
        sub_type: str | None = None,
        parameters: dict[str, str] | None = None,
    ) -> Self:
        """
        Copy the MIME type with the given parameters updated.
        """
        main_type = main_type or self.main_type
        sub_type = sub_type or self.sub_type
        parameters = parameters or self.parameters
        parameters = {
            **self.parameters,
            **(parameters or {})
        }
        return self.__class__(
            main_type, sub_type, parameters
        )


try:
    from pydantic import BeforeValidator, PlainSerializer
except ImportError: pass
else:
    MimeType_str = Annotated[
        MimeType,
        BeforeValidator(MimeType.parse),
        PlainSerializer(str, when_used='json')
    ]
    """
        A MIME type backed by a JSON string.
    """


MIME_BINARY = MimeType.parse('application/octet-stream')
MIME_PLAINTEXT_UTF8 = MimeType.parse('text/plain; charset=utf-8')
MIME_PLAINTEXT = MimeType.parse('text/plain')
MIME_JSON = MimeType.parse('application/json')
MIME_YAML = MimeType.parse('application/yaml')
MIME_MARKDOWN = MimeType.parse('text/markdown')
