"""ORM-neutral high-level API for pyrsql."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pyrsql.core.query import Query

if TYPE_CHECKING:
    from pyrsql.core.compiler import CompiledArtifact
    from pyrsql.core.options import QueryOptions
    from pyrsql.orms.base import ORM

_TargetT = TypeVar("_TargetT")
_ModelT = TypeVar("_ModelT")


def parse(query_text: str, *, options: QueryOptions | None = None) -> Query:
    """Parses raw RSQL text into a query object.

    Args:
        query_text: Raw RSQL text to parse.
        options: Optional query configuration.

    Returns:
        A parsed query object.
    """
    return Query.parse(query_text, options=options)


def compile(  # noqa: A001
    query_text: str,
    *,
    orm: ORM,
    options: QueryOptions | None = None,
) -> CompiledArtifact:
    """Compiles raw RSQL text using the provided ORM.

    Args:
        query_text: Raw RSQL text to compile.
        orm: ORM adapter used to compile the query.
        options: Optional query configuration.

    Returns:
        The ORM-specific compiled query.
    """
    return parse(query_text, options=options).compile(orm=orm)


def apply(
    target: _TargetT,
    model: type[_ModelT],
    query_text: str,
    *,
    orm: ORM,
    options: QueryOptions | None = None,
) -> _TargetT:
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


__all__ = ("apply", "compile", "parse")
