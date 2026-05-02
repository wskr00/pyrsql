"""Backend-neutral high-level API for pyrsql."""

# pylint: disable=redefined-builtin

from typing import Any

from pyrsql.backends.base import Backend
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.core.query import Query


def parse(query_text: str, *, options: QueryOptions | None = None) -> Query:
    """Builds a query object from raw RSQL text."""
    return Query.parse(query_text, options=options)


def compile(
    query_text: str,
    *,
    backend: Backend,
    options: QueryOptions | None = None,
    ) -> CompilationResult:
    """Compiles a query string using the provided backend."""
    return parse(query_text, options=options).compile(backend=backend)


def apply(
    target: Any,
    model: type[Any],
    query_text: str,
    *,
    backend: Backend,
    options: QueryOptions | None = None,
) -> Any:
    """Applies a query string to a backend-specific target."""
    return compile(
        query_text,
        backend=backend,
        options=options,
    ).apply(target=target, model=model)
