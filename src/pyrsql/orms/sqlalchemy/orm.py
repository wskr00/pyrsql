"""SQLAlchemy ORM entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from pyrsql.orms import base
from pyrsql.orms.sqlalchemy.compiled import SQLAlchemyCompiledQuery
from pyrsql.orms.sqlalchemy.compiled_page import SQLAlchemyCompiledPageRequest
from pyrsql.orms.sqlalchemy.compiled_sort import SQLAlchemyCompiledSort
from pyrsql.orms.sqlalchemy.sorter import SQLAlchemySortTranslator
from pyrsql.orms.sqlalchemy.translator import SQLAlchemyExpressionTranslator

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyrsql.core.page import PageRequest
    from pyrsql.core.query import Query
    from pyrsql.core.sort import Sort
    from pyrsql.orms.sqlalchemy.custom import SQLAlchemyCustomPredicate


class SQLAlchemyORM(base.ORM):
    """ORM adapter for SQLAlchemy 2.0 integration."""

    __slots__ = ("_sort_translator", "_translator")

    def __init__(
        self,
        *,
        translator: SQLAlchemyExpressionTranslator | None = None,
        sort_translator: SQLAlchemySortTranslator | None = None,
        custom_predicates: (
            Mapping[str, SQLAlchemyCustomPredicate] | None
        ) = None,
    ) -> None:
        """Creates a SQLAlchemy ORM adapter.

        Raises:
            ValueError: If custom predicates are provided together with an
                explicit translator.
        """
        if translator is not None and custom_predicates is not None:
            raise ValueError(
                "custom_predicates cannot be provided when translator is "
                "passed explicitly.",
            )
        self._translator = translator or SQLAlchemyExpressionTranslator(
            custom_predicates=custom_predicates,
        )
        self._sort_translator = sort_translator or SQLAlchemySortTranslator()

    @property
    def name(self) -> str:
        """Returns the ORM name.

        Returns:
            The stable ORM name.
        """
        return "sqlalchemy"

    def compile_query(self, query: Query) -> SQLAlchemyCompiledQuery:
        """Compiles a pyrsql query for SQLAlchemy.

        Returns:
            A SQLAlchemy-specific compiled query object.
        """
        return SQLAlchemyCompiledQuery(
            expression=query.bound_expression,
            options=query.options,
            translator=self._translator,
        )

    def compile_sort(self, sort: Sort) -> SQLAlchemyCompiledSort:
        """Compiles a pyrsql sort for SQLAlchemy.

        Returns:
            A SQLAlchemy-specific compiled sort object.
        """
        return SQLAlchemyCompiledSort(
            sort_plan=sort.bound_sort,
            options=sort.options,
            translator=self._sort_translator,
        )

    @override
    def compile_page_request(
        self,
        page_request: PageRequest,
    ) -> SQLAlchemyCompiledPageRequest:
        """Compiles a pyrsql page request for SQLAlchemy.

        Returns:
            A SQLAlchemy-specific compiled page request object.
        """
        return SQLAlchemyCompiledPageRequest(page=page_request.bound_page)
