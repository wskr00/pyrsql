"""ORM-neutral high-level API for pyrsql."""

# pylint: disable=redefined-builtin

from typing import Any

from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.core.query import Query
from pyrsql.orms.base import ORM


def parse(query_text: str, *, options: QueryOptions | None = None) -> Query:
    """Parses raw RSQL text into a query object.

    Args:
        query_text: Raw RSQL text to parse.
        options: Optional query configuration.

    Returns:
        A parsed query object.
    """
    return Query.parse(query_text, options=options)


def compile(
    query_text: str,
    *,
    orm: ORM,
    options: QueryOptions | None = None,
) -> CompilationResult:
    """Compiles raw RSQL text using the provided ORM.

    Args:
        query_text: Raw RSQL text to compile.
        orm: ORM adapter used to compile the query.
        options: Optional query configuration.

    Returns:
        The ORM-specific compilation result.
    """
    return parse(query_text, options=options).compile(orm=orm)


def apply(
    target: Any,
    model: type[Any],
    query_text: str,
    *,
    orm: ORM,
    options: QueryOptions | None = None,
) -> Any:
    """Applies raw RSQL text to an ORM-specific target.

    Args:
        target: ORM-specific target to mutate.
        model: ORM model class used to resolve the query.
        query_text: Raw RSQL text to apply.
        orm: ORM adapter used to compile the query.
        options: Optional query configuration.

    Returns:
        The value returned by the ORM-specific apply operation.
    """
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
