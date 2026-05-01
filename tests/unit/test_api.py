"""Sanity tests for the backend-neutral public API."""

import pyrsql
from pyrsql.backends.sqlalchemy import SQLAlchemyBackend


def test_parse_returns_query_object() -> None:
    """Ensures the package-level parse helper builds a query object."""
    query = pyrsql.parse("name==demo")
    assert query.text == "name==demo"
    assert query.options.strict_equality is False


def test_compile_uses_backend_name() -> None:
    """Ensures compilation returns the selected backend metadata."""
    compilation = pyrsql.compile(
        "name==demo",
        backend=SQLAlchemyBackend(),
    )
    assert compilation.backend_name == "sqlalchemy"
