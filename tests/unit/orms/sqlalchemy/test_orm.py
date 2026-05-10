"""Unit tests for the SQLAlchemy ORM entry point."""

from typing import TYPE_CHECKING

import pytest

from pyrsql.orms.sqlalchemy.orm import SQLAlchemyORM
from pyrsql.orms.sqlalchemy.translator import SQLAlchemyExpressionTranslator

if TYPE_CHECKING:
    from pyrsql.orms.sqlalchemy.custom import SQLAlchemyCustomPredicate


def test_sqlalchemy_orm_rejects_translator_and_custom_predicates() -> None:
    """Rejects ambiguous translator and custom-predicate configuration."""
    translator = SQLAlchemyExpressionTranslator()
    custom_predicates: dict[str, SQLAlchemyCustomPredicate] = {}

    with pytest.raises(
        ValueError,
        match="custom_predicates cannot be provided",
    ):
        SQLAlchemyORM(
            translator=translator,
            custom_predicates=custom_predicates,
        )
