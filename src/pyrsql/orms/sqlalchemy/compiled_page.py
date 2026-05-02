"""Compiled pagination support for SQLAlchemy."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.sql import Select

from pyrsql.core.page import PageRequest


@dataclass(frozen=True, slots=True)
class SQLAlchemyCompiledPageRequest:
    """Compiled SQLAlchemy pagination plan."""

    page_request: PageRequest

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled page request to a SQLAlchemy Select."""
        del model
        if not isinstance(target, Select):
            raise TypeError("SQLAlchemy ORM expects a sqlalchemy.sql.Select.")
        return target.limit(self.page_request.limit).offset(
            self.page_request.offset
        )
