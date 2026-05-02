"""Compiled pagination support for SQLAlchemy."""

from dataclasses import dataclass

from pyrsql.core.page import PageRequest
from pyrsql.orms.sqlalchemy.statement import require_sqlalchemy_select
from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


@dataclass(frozen=True, slots=True)
class SQLAlchemyCompiledPageRequest:
    """Compiled SQLAlchemy pagination plan."""

    page_request: PageRequest

    def apply(
        self,
        target: SQLAlchemySelect | object,
        model: SQLAlchemyModel,
    ) -> SQLAlchemySelect:
        """Applies the compiled page request to a SQLAlchemy Select."""
        del model
        statement = require_sqlalchemy_select(target)
        return statement.limit(self.page_request.limit).offset(
            self.page_request.offset
        )
