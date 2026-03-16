from contextlib import contextmanager
from io import TextIOWrapper
from pathlib import Path
from typing import BinaryIO, Iterator, TextIO


__all__ = [
    'resolve_path',
    'text_writer',
]


def resolve_path(
    path: Path|str,
    *locations: Path|str
) -> Path:
    """
        Resolves a path relative to a list of locations.
        If the path is absolute, returns it as-is.
        If the path is relative, searches the locations
        for the path, and returns the first match.
        If the path is not found, raises a FileNotFoundError.
    """
    if isinstance(path, str):
        path = Path(path)
    if path.is_absolute():
        return path
    for search_path in locations:
        if isinstance(search_path, str):
            search_path = Path(search_path)
        candidate = search_path / path
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Path not found: {path}")


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

