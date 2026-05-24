"""Unit tests for SQLAlchemy statement helpers."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from pyrsql.core.joins import JoinHint
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError
from pyrsql.orms.sqlalchemy.statement import (
    apply_relationship_joins,
    require_sqlalchemy_select,
)
from pyrsql.orms.sqlalchemy.types import SQLAlchemyJoinPlan

from .conftest import User

pytestmark = pytest.mark.sqlalchemy


def test_require_sqlalchemy_select_rejects_non_select_target() -> None:
    """Rejects non-Select targets with a clear error."""
    with pytest.raises(TypeError, match=r"SQLAlchemy ORM expects"):
        require_sqlalchemy_select(object())


def test_apply_relationship_joins_deduplicates_repeated_join_plan() -> None:
    """Applies one relationship join once even when repeated."""
    statement = apply_relationship_joins(
        select(User),
        (
            JoinPlanFixtures.company_inner(),
            JoinPlanFixtures.company_inner(),
        ),
    )

    sql = str(statement)
    assert sql.count("JOIN company") == 1


def test_apply_relationship_joins_rejects_right_join_hint() -> None:
    """Rejects unsupported RIGHT join hints explicitly."""
    with pytest.raises(SQLAlchemyORMError, match=r"RIGHT joins"):
        apply_relationship_joins(
            select(User),
            (JoinPlanFixtures.company_inner(),),
            join_hints={"User.company": JoinHint.RIGHT},
        )


class JoinPlanFixtures:
    """Factory helpers for small statement-helper tests."""

    @staticmethod
    def company_inner():
        return SQLAlchemyJoinPlan(
            key="User.company",
            attribute=User.company,
            default_hint=JoinHint.INNER,
            is_collection=False,
        )
