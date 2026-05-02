"""SQLAlchemy backend entry point."""

from typing import Mapping
from typing import TYPE_CHECKING

from pyrsql.backends import base
from pyrsql.backends.sqlalchemy.compiled_page import (
    SQLAlchemyCompiledPageRequest,
)
from pyrsql.backends.sqlalchemy.compiled import SQLAlchemyCompiledQuery
from pyrsql.backends.sqlalchemy.custom import SQLAlchemyCustomPredicate
from pyrsql.backends.sqlalchemy.compiled_sort import SQLAlchemyCompiledSort
from pyrsql.backends.sqlalchemy.sorter import SQLAlchemySortTranslator
from pyrsql.backends.sqlalchemy.translator import SQLAlchemyExpressionTranslator

if TYPE_CHECKING:
    from pyrsql.core.page import PageRequest
    from pyrsql.core.query import Query
    from pyrsql.core.sort import Sort


class SQLAlchemyBackend(base.Backend):
    """Backend adapter for SQLAlchemy 2.0 integration."""

    def __init__(
        self,
        *,
        translator: SQLAlchemyExpressionTranslator | None = None,
        sort_translator: SQLAlchemySortTranslator | None = None,
        custom_predicates: (
            Mapping[str, SQLAlchemyCustomPredicate] | None
        ) = None,
    ) -> None:
        self._translator = translator or SQLAlchemyExpressionTranslator(
            custom_predicates=custom_predicates,
        )
        self._sort_translator = sort_translator or SQLAlchemySortTranslator()

    @property
    def name(self) -> str:
        """Returns the backend name."""
        return "sqlalchemy"

    def compile_query(self, query: "Query") -> base.CompiledQuery:
        """Compiles a pyrsql query for SQLAlchemy."""
        if query.semantic_expression is None:
            raise ValueError("Query must carry a semantic expression.")
        return SQLAlchemyCompiledQuery(
            expression=query.semantic_expression,
            options=query.options,
            translator=self._translator,
        )

    def compile_sort(self, sort: "Sort") -> base.CompiledSort:
        """Compiles a pyrsql sort for SQLAlchemy."""
        return SQLAlchemyCompiledSort(
            fields=sort.semantic_fields,
            options=sort.options,
            translator=self._sort_translator,
        )

    def compile_page_request(
        self,
        page_request: "PageRequest",
    ) -> base.CompiledPageRequest:
        """Compiles a pyrsql page request for SQLAlchemy."""
        return SQLAlchemyCompiledPageRequest(page_request=page_request)
