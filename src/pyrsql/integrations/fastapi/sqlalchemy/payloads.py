"""Shared payload types for FastAPI + SQLAlchemy integrations."""

import msgspec

from pyrsql.orms.sqlalchemy.statement import require_sqlalchemy_select
from pyrsql.orms.sqlalchemy.types import SQLAlchemySelect


class SQLAlchemyPaginatedSelect(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Carries the list and count statements for a paginated query flow."""

    statement: SQLAlchemySelect
    count_statement: SQLAlchemySelect

    def __post_init__(self) -> None:
        """Validates the carried SQLAlchemy statements."""
        require_sqlalchemy_select(self.statement)
        require_sqlalchemy_select(self.count_statement)
