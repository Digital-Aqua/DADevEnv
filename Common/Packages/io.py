from contextlib import contextmanager
from io import TextIOWrapper
from typing import BinaryIO, Iterator, TextIO


__all__ = [
    'text_writer',
]


@contextmanager
def text_writer(
    buffer: BinaryIO,
    encoding: str = 'utf-8',
    *,
    errors: str | None = None,
    newline: str | None = None,
) -> Iterator[TextIO]:
    """
        Wrap a binary writer as text, then detach on exit
        so the buffer stays open.
    """
    text_writer = TextIOWrapper(
        buffer,
        encoding=encoding,
        errors=errors,
        newline=newline,
    )
    try:
        yield text_writer.__enter__()
    finally:
        text_writer.flush()
        text_writer.detach()
