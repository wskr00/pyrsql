"""ORM-neutral high-level API for pyrsql."""

# pylint: disable=redefined-builtin

from typing import Any

from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.core.query import Query
from pyrsql.orms.base import ORM


def parse(query_text: str, *, options: QueryOptions | None = None) -> Query:
    """Builds a query object from raw RSQL text."""
    return Query.parse(query_text, options=options)


def compile(
    query_text: str,
    *,
    orm: ORM,
    options: QueryOptions | None = None,
) -> CompilationResult:
    """Compiles a query string using the provided orm."""
    return parse(query_text, options=options).compile(orm=orm)


def apply(
    target: Any,
    model: type[Any],
    query_text: str,
    *,
    orm: ORM,
    options: QueryOptions | None = None,
) -> Any:
    """Applies a query string to an ORM-specific target."""
    return compile(
        query_text,
        orm=orm,
        options=options,
    ).apply(target=target, model=model)


__all__ = [
    "apply",
    "compile",
    "parse",
]
