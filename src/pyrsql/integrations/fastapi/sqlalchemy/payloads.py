"""Shared payload types for FastAPI + SQLAlchemy integrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
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
