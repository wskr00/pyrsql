"""SQLAlchemy ORM entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from pyrsql.orms import base
from pyrsql.orms.sqlalchemy.compiled_page import SQLAlchemyCompiledPageRequest
from pyrsql.orms.sqlalchemy.compiled_query import SQLAlchemyCompiledQuery
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
        """Creates a SQLAlchemy ORM adapter."""
        self._translator = self._build_translator(
            translator=translator,
            custom_predicates=custom_predicates,
        )
        self._sort_translator = (
            SQLAlchemySortTranslator()
            if sort_translator is None
            else sort_translator
        )

    @staticmethod
    def _build_translator(
        *,
        translator: SQLAlchemyExpressionTranslator | None,
        custom_predicates: (Mapping[str, SQLAlchemyCustomPredicate] | None),
    ) -> SQLAlchemyExpressionTranslator:
        """Builds the effective query translator.

        Returns:
            The translator to use for query compilation.

        Raises:
            ValueError: If custom predicates are combined with an explicit
                translator.
        """
        if translator is not None:
            if custom_predicates is not None:
                raise ValueError(
                    "custom_predicates cannot be provided when translator is "
                    "passed explicitly.",
                )
            return translator
        return SQLAlchemyExpressionTranslator(
            custom_predicates=custom_predicates,
        )

    @property
    def name(self) -> str:
        """Returns the ORM name.

        Returns:
            The stable ORM name.
        """
        return "sqlalchemy"

    def compile_query(self, query: Query) -> SQLAlchemyCompiledQuery:  # type: ignore[override]
        """Compiles a pyrsql query for SQLAlchemy.

        Returns:
            A SQLAlchemy-specific compiled query object.
        """
        return SQLAlchemyCompiledQuery(
            expression=query.bound_expression,
            options=query.options,
            translator=self._translator,
        )

    def compile_sort(self, sort: Sort) -> SQLAlchemyCompiledSort:  # type: ignore[override]
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
    def compile_page_request(  # type: ignore[override]
        self,
        page_request: PageRequest,
    ) -> SQLAlchemyCompiledPageRequest:
        """Compiles a pyrsql page request for SQLAlchemy.

        Returns:
            A SQLAlchemy-specific compiled page request object.
        """
        return SQLAlchemyCompiledPageRequest(page=page_request.bound_page)
