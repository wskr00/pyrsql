"""Performance regression tests for ORM path resolution."""

from __future__ import annotations

from timeit import timeit

import pytest

pytest.importorskip("sqlalchemy")

from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.orms.sqlalchemy.resolver import SQLAlchemyPathResolver

from .conftest import Company, User

pytestmark = [pytest.mark.performance, pytest.mark.sqlalchemy]


@pytest.fixture(scope="session")
def path_resolver() -> SQLAlchemyPathResolver:
    """Provides a session-scoped path resolver for benchmarks."""
    return SQLAlchemyPathResolver()


def test_direct_column_resolution_remains_fast(
    path_resolver: SQLAlchemyPathResolver,
) -> None:
    """Keeps direct column resolution within budget."""
    elapsed = timeit(
        lambda: path_resolver.resolve(User, "name"),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 50.0


def test_relationship_path_resolution_remains_fast(
    path_resolver: SQLAlchemyPathResolver,
) -> None:
    """Keeps relationship path resolution within budget."""
    elapsed = timeit(
        lambda: path_resolver.resolve(User, "company.name"),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 100.0


def test_field_mapping_expansion_remains_fast(
    path_resolver: SQLAlchemyPathResolver,
) -> None:
    """Keeps field mapping expansion within budget."""
    policy = FieldPolicySet(
        field_mapping={"companyName": "company.name"},
        field_whitelist=frozenset(),
        field_blacklist=frozenset(),
        model_field_mapping={Company: {"companyName": "name"}},
        model_field_whitelist={},
        model_field_blacklist={},
    )
    elapsed = timeit(
        lambda: path_resolver.resolve(
            User,
            "company.companyName",
            field_policy=policy,
        ),
        number=5000,
    )
    average_microseconds = elapsed / 5000 * 1_000_000
    assert average_microseconds < 150.0
