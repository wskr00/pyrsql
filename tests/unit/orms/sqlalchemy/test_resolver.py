"""Unit tests for SQLAlchemy path resolution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import time

import pytest

from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.core.joins import JoinHint
from pyrsql.core.json.path import JSONPath
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyPathResolutionError
from pyrsql.orms.sqlalchemy.introspection import SQLAlchemyModelInspector
from pyrsql.orms.sqlalchemy.resolver import SQLAlchemyPathResolver

from .conftest import Address, Company, Event, User

pytestmark = pytest.mark.sqlalchemy


@pytest.mark.parametrize(
    ("model", "attribute_name", "expected_python_type", "is_relationship"),
    [
        pytest.param(User, "name", str, False, id="column"),
        pytest.param(User, "company", Company, True, id="relationship"),
        pytest.param(
            User,
            "addresses",
            Address,
            True,
            id="collection-relationship",
        ),
    ],
)
def test_model_inspector_reads_attribute_metadata(
    model_inspector: SQLAlchemyModelInspector,
    model: type[object],
    attribute_name: str,
    expected_python_type: type[object],
    is_relationship: bool,
) -> None:
    """Inspects mapped column and relationship metadata."""
    mapped_attribute = model_inspector.get_mapped_attribute(
        model,
        attribute_name,
    )

    assert mapped_attribute.name == attribute_name
    assert mapped_attribute.python_type is expected_python_type
    assert (mapped_attribute.mapper is not None) is is_relationship


def test_model_inspector_marks_collection_relationships(
    model_inspector: SQLAlchemyModelInspector,
) -> None:
    """Marks collection-based relationships explicitly."""
    mapped_attribute = model_inspector.get_mapped_attribute(User, "addresses")

    assert mapped_attribute.is_collection is True
    assert mapped_attribute.mapper is not None
    assert mapped_attribute.mapper.class_ is Address


def test_model_inspector_attribute_cache_is_safe_under_concurrency(
    model_inspector: SQLAlchemyModelInspector,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds one cached attribute description under concurrent access."""
    original_inspect_model = model_inspector.inspect_model
    call_count = 0

    def slow_inspect_model(
        self: SQLAlchemyModelInspector,
        model: type[object],
    ):
        nonlocal call_count
        call_count += 1
        time.sleep(0.02)
        return original_inspect_model(model)

    monkeypatch.setattr(
        SQLAlchemyModelInspector,
        "inspect_model",
        slow_inspect_model,
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        attributes = list(
            executor.map(
                lambda _: model_inspector.get_mapped_attribute(User, "name"),
                range(8),
            )
        )

    assert call_count == 1
    assert all(attribute is attributes[0] for attribute in attributes)


@pytest.mark.parametrize(
    (
        "field_path",
        "expected_join_count",
        "expected_leaf_model",
        "expected_python_type",
        "expected_json_path",
        "expected_is_json",
    ),
    [
        pytest.param(
            "name",
            0,
            User,
            str,
            JSONPath(),
            False,
            id="direct-column",
        ),
        pytest.param(
            "company.name",
            1,
            Company,
            str,
            JSONPath(),
            False,
            id="relationship-path",
        ),
        pytest.param(
            "addresses.city",
            1,
            Address,
            str,
            JSONPath(),
            False,
            id="collection-relationship-path",
        ),
        pytest.param(
            "payload.user.id",
            0,
            Event,
            None,
            JSONPath(segments=("user", "id")),
            True,
            id="nested-json-path",
        ),
        pytest.param(
            "payload",
            0,
            Event,
            dict,
            JSONPath(),
            True,
            id="root-json-column",
        ),
    ],
)
def test_path_resolver_resolves_supported_field_paths(
    path_resolver: SQLAlchemyPathResolver,
    *,
    field_path: str,
    expected_join_count: int,
    expected_leaf_model: type[object],
    expected_python_type: type[object] | None,
    expected_json_path: JSONPath,
    expected_is_json: bool,
) -> None:
    """Resolves direct, relationship, collection, and JSON paths."""
    model = Event if field_path.startswith("payload") else User
    resolved = path_resolver.resolve(model, field_path)

    assert resolved.field_path == field_path
    assert len(resolved.joins) == expected_join_count
    assert resolved.leaf_model is expected_leaf_model
    assert resolved.python_type is expected_python_type
    assert resolved.json_path == expected_json_path
    assert resolved.is_json is expected_is_json


def test_path_resolver_resolves_relationship_joins_with_metadata(
    path_resolver: SQLAlchemyPathResolver,
) -> None:
    """Resolves relationship joins with stable join metadata."""
    resolved = path_resolver.resolve(User, "company.name")

    assert len(resolved.joins) == 1
    assert resolved.joins[0].attribute is User.company
    assert resolved.joins[0].key == "User.company"
    assert resolved.joins[0].default_hint is JoinHint.INNER
    assert resolved.joins[0].is_collection is False


def test_path_resolver_default_cache_is_safe_under_concurrency(
    path_resolver: SQLAlchemyPathResolver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds one cached resolved path under concurrent access."""
    original_resolve = SQLAlchemyPathResolver._resolve_with_field_policy
    call_count = 0

    def slow_resolve(
        self: SQLAlchemyPathResolver,
        *args: object,
        **kwargs: object,
    ):
        nonlocal call_count
        call_count += 1
        time.sleep(0.02)
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(
        SQLAlchemyPathResolver,
        "_resolve_with_field_policy",
        slow_resolve,
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        resolved_paths = list(
            executor.map(
                lambda _: path_resolver.resolve(User, "company.name"),
                range(8),
            )
        )

    assert call_count == 1
    assert all(resolved is resolved_paths[0] for resolved in resolved_paths)


def test_path_resolver_marks_collection_relationship_joins(
    path_resolver: SQLAlchemyPathResolver,
) -> None:
    """Marks collection joins when traversing one-to-many relationships."""
    resolved = path_resolver.resolve(User, "addresses.city")

    assert len(resolved.joins) == 1
    assert resolved.joins[0].attribute is User.addresses
    assert resolved.joins[0].is_collection is True


@pytest.mark.parametrize(
    "field_path",
    [
        pytest.param("company", id="terminal-relationship"),
        pytest.param("name.value", id="traverse-through-column"),
        pytest.param("company..name", id="empty-segment"),
    ],
)
def test_path_resolver_rejects_invalid_field_paths(
    path_resolver: SQLAlchemyPathResolver,
    field_path: str,
) -> None:
    """Rejects invalid relationship and dotted-path shapes."""
    with pytest.raises(SQLAlchemyPathResolutionError):
        path_resolver.resolve(User, field_path)


def test_path_resolver_applies_model_field_mapping(
    path_resolver: SQLAlchemyPathResolver,
) -> None:
    """Resolves per-model field aliases during path traversal."""
    resolved = path_resolver.resolve(
        User,
        "company.companyName",
        field_policy=FieldPolicySet(
            field_mapping={},
            field_whitelist=frozenset(),
            field_blacklist=frozenset(),
            model_field_mapping={Company: {"companyName": "name"}},
            model_field_whitelist={},
            model_field_blacklist={},
        ),
    )

    assert resolved.python_type is str
    assert resolved.leaf_model is Company


def test_path_resolver_enforces_model_field_whitelist(
    path_resolver: SQLAlchemyPathResolver,
) -> None:
    """Rejects leaf attributes outside model-specific whitelists."""
    with pytest.raises(SQLAlchemyPathResolutionError):
        path_resolver.resolve(
            User,
            "company.name",
            field_policy=FieldPolicySet(
                field_mapping={},
                field_whitelist=frozenset(),
                field_blacklist=frozenset(),
                model_field_mapping={},
                model_field_whitelist={Company: frozenset({"id"})},
                model_field_blacklist={},
            ),
        )
