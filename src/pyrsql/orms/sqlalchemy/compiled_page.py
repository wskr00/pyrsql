"""Compiled pagination support for SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from pyrsql.orms.sqlalchemy.statement import require_sqlalchemy_select

if TYPE_CHECKING:
    from pyrsql.core.page import PageRequest
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


class SQLAlchemyCompiledPageRequest(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Compiled SQLAlchemy pagination plan.

    Attributes:
        page_request: Pagination request to apply to a select statement.
    """

    page_request: PageRequest

    def apply(
        self,
        target: SQLAlchemySelect,
        model: SQLAlchemyModel,
    ) -> SQLAlchemySelect:
        """Applies the compiled page request to a SQLAlchemy Select.

        Args:
            target: SQLAlchemy select statement to mutate.
            model: SQLAlchemy mapped class. It is unused, but the signature
                matches the other compiled plans.

        Returns:
            A SQLAlchemy select with limit and offset applied.
        """
        del model
        statement = require_sqlalchemy_select(target)
        return statement.limit(self.page_request.limit).offset(
            self.page_request.offset,
        )
