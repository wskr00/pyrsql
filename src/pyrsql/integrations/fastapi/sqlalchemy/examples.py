"""OpenAPI example generation helpers for FastAPI SQLAlchemy resources."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Final, cast
from uuid import UUID

from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.orms.sqlalchemy.resolver import SQLAlchemyPathResolver

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel

_DEFAULT_PATH_RESOLVER: Final = SQLAlchemyPathResolver()
_DEFAULT_STRING_EXAMPLE = "demo"
_DEFAULT_INTEGER_EXAMPLE = "1"
_DEFAULT_FLOAT_EXAMPLE = "1.5"
_DEFAULT_BOOLEAN_EXAMPLE = "true"
_DEFAULT_DATE_EXAMPLE = "2026-01-01"
_DEFAULT_DATETIME_EXAMPLE = "2026-01-01T10:30:00"
_DEFAULT_UUID_EXAMPLE = "12345678-1234-5678-1234-567812345678"


def normalize_default_sort(default_sort: str) -> str:
    """Normalizes shorthand default sort expressions.

    Returns:
        The normalized default sort expression.

    Raises:
        ValueError: If the provided default sort is blank.
    """
    stripped = default_sort.strip()
    if not stripped:
        raise ValueError("default_sort must not be blank.")
    if "," in stripped:
        return stripped
    if stripped.startswith("-") and len(stripped) > 1:
        return f"{stripped[1:]},desc"
    if stripped.startswith("+") and len(stripped) > 1:
        return f"{stripped[1:]},asc"
    return stripped


def _build_example_resolution_policy(
    field_policy: FieldPolicySet | None,
) -> FieldPolicySet | None:
    """Builds the minimal policy needed for example type resolution.

    Returns:
        A reduced field policy carrying only model-specific field mappings.
    """
    if field_policy is None or not field_policy.model_field_mapping:
        return None
    return FieldPolicySet(
        field_whitelist=frozenset(),
        field_blacklist=frozenset(),
        model_field_mapping=field_policy.model_field_mapping,
        model_field_whitelist={},
        model_field_blacklist={},
    )


def filter_example_value(
    python_type: type[Any] | None,
    *,
    is_json: bool = False,
) -> str:
    """Builds one scalar filter example literal from a resolved Python type.

    Returns:
        A filter-compatible scalar literal.
    """
    if is_json or python_type is None:
        return _DEFAULT_STRING_EXAMPLE
    if issubclass(python_type, Enum):
        return _enum_filter_example_value(python_type)
    if issubclass(python_type, bool):
        return _DEFAULT_BOOLEAN_EXAMPLE
    if issubclass(python_type, int):
        return _DEFAULT_INTEGER_EXAMPLE
    if issubclass(python_type, (float, Decimal)):
        return _DEFAULT_FLOAT_EXAMPLE
    if issubclass(python_type, dt.datetime):
        return _DEFAULT_DATETIME_EXAMPLE
    if issubclass(python_type, dt.date):
        return _DEFAULT_DATE_EXAMPLE
    if issubclass(python_type, UUID):
        return _DEFAULT_UUID_EXAMPLE
    return _DEFAULT_STRING_EXAMPLE


def _enum_filter_example_value(enum_type: type[Any]) -> str:
    """Builds one filter example literal for an enum type.

    Returns:
        A filter-compatible enum literal.
    """
    typed_enum = cast("type[Enum]", enum_type)
    try:
        first_member = next(iter(typed_enum))
    except StopIteration:
        return _DEFAULT_STRING_EXAMPLE
    enum_value = first_member.value
    if isinstance(enum_value, bool):
        return "true" if enum_value else "false"
    return str(enum_value)


def format_filter_example(
    model: SQLAlchemyModel,
    field_path: str,
    *,
    field_mapping: Mapping[str, str],
    field_policy: FieldPolicySet | None,
    path_resolver: SQLAlchemyPathResolver,
) -> str:
    """Formats one automatic filter example from resolved ORM metadata.

    Returns:
        One automatic filter expression example.
    """
    resolved_path = path_resolver.resolve(
        model,
        field_mapping.get(field_path, field_path),
        field_policy=field_policy,
    )
    example_value = filter_example_value(
        resolved_path.python_type,
        is_json=resolved_path.is_json,
    )
    return f"{field_path}=={example_value}"


def build_filter_examples(
    model: SQLAlchemyModel,
    filterable_fields: set[str] | frozenset[str] | None,
    *,
    field_mapping: Mapping[str, str] | None = None,
    field_policy: FieldPolicySet | None = None,
    path_resolver: SQLAlchemyPathResolver | None = None,
) -> dict[str, dict[str, object]]:
    """Builds automatic filter examples from declarative field config.

    Returns:
        Automatic OpenAPI examples for filter parameters.
    """
    if not filterable_fields:
        return {}

    active_field_mapping = {} if field_mapping is None else field_mapping
    active_path_resolver = (
        _DEFAULT_PATH_RESOLVER if path_resolver is None else path_resolver
    )
    resolution_policy = _build_example_resolution_policy(field_policy)
    examples: dict[str, dict[str, object]] = {}
    for field_path in sorted(filterable_fields)[:3]:
        key = field_path.replace(".", "_")
        examples[f"filter_by_{key}"] = {
            "summary": f"Filter by {field_path}",
            "value": format_filter_example(
                model,
                field_path,
                field_mapping=active_field_mapping,
                field_policy=resolution_policy,
                path_resolver=active_path_resolver,
            ),
        }
    return examples


def build_sort_examples(
    sortable_fields: set[str] | frozenset[str] | None,
    default_sort: str | None,
) -> dict[str, dict[str, object]]:
    """Builds automatic sort examples from declarative sort config.

    Returns:
        Automatic OpenAPI examples for sort parameters.
    """
    examples: dict[str, dict[str, object]] = {}
    if sortable_fields:
        first_field = min(sortable_fields)
        example_key = first_field.replace(".", "_")
        examples[f"sort_by_{example_key}_asc"] = {
            "summary": f"Sort by {first_field} ascending",
            "value": f"{first_field},asc",
        }
    if default_sort is not None:
        examples["default_sort"] = {
            "summary": "Default sort",
            "value": normalize_default_sort(default_sort),
        }
    return examples


def merge_openapi_examples(
    generated: dict[str, dict[str, object]],
    explicit: dict[str, dict[str, object]] | None,
) -> dict[str, dict[str, object]]:
    """Merges automatic and explicit OpenAPI examples.

    Returns:
        The merged OpenAPI example mapping.
    """
    if explicit is None:
        return generated
    merged = dict(generated)
    merged.update(explicit)
    return merged
