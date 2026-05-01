"""SQLAlchemy backend entry point."""

from typing import Any

from pyrsql.backends import base


class _SQLAlchemyCompiledQuery(base.CompiledQuery):
    """Placeholder compiled query for the SQLAlchemy backend."""

    def __init__(self, query_text: str) -> None:
        self._query_text = query_text

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled result to a SQLAlchemy target."""
        del target, model  # Unused until the translator exists.
        raise NotImplementedError(
            "SQLAlchemy query application is not implemented yet for "
            f"query: {self._query_text!r}"
        )


class SQLAlchemyBackend(base.Backend):
    """Backend adapter for SQLAlchemy 2.0 integration."""

    @property
    def name(self) -> str:
        """Returns the backend name."""
        return "sqlalchemy"

    def compile_query(self, query: "Query") -> base.CompiledQuery:
        """Compiles a pyrsql query for SQLAlchemy."""
        return _SQLAlchemyCompiledQuery(query_text=query.text)


from pyrsql.core.query import Query
