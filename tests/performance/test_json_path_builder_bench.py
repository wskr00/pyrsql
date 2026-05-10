"""Performance regression tests for JSON path expression building."""

from __future__ import annotations

from timeit import timeit
from typing import Any

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import column

from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.orms.sqlalchemy.json_path import (
    SQLAlchemyJSONPathExpressionBuilder,
)

pytestmark = [pytest.mark.performance, pytest.mark.sqlalchemy]


@pytest.fixture(scope="session")
def json_path_builder() -> SQLAlchemyJSONPathExpressionBuilder:
    """Provides a session-scoped JSON path expression builder."""
    return SQLAlchemyJSONPathExpressionBuilder()


def test_json_path_filter_expression_remains_fast(
    json_path_builder: SQLAlchemyJSONPathExpressionBuilder,
    pg_dialect: Any,
) -> None:
    """Keeps JSON path filter expression building within budget."""
    comparison = JSONPathComparison.from_raw_arguments(
        path=JSONPath(segments=("payload", "user", "id")),
        operator_name="equal",
        raw_arguments=(("1", False),),
    )

    def _build() -> None:
        predicate = json_path_builder.build_filter_expression(
            column("payload"),
            comparison,
        )
        predicate.compile(dialect=pg_dialect)

    elapsed = timeit(_build, number=5_000)
    average_microseconds = elapsed / 5_000 * 1_000_000
    assert average_microseconds < 300.0


def test_json_path_document_filter_expression_remains_fast(
    json_path_builder: SQLAlchemyJSONPathExpressionBuilder,
    pg_dialect: Any,
) -> None:
    """Keeps JSON path document filter expression building within budget."""
    comparison = JSONPathComparison.from_raw_arguments(
        path=JSONPath(segments=("payload",)),
        operator_name="equal",
        raw_arguments=(('{"id": 1}', True),),
    )

    def _build() -> None:
        predicate = json_path_builder.build_document_filter_expression(
            column("payload"),
            comparison,
        )
        predicate.compile(dialect=pg_dialect)

    elapsed = timeit(_build, number=5_000)
    average_microseconds = elapsed / 5_000 * 1_000_000
    assert average_microseconds < 300.0
