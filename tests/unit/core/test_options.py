"""Unit tests for ORM-neutral core options and policies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from pyrsql.core.conversion import (
    DEFAULT_FIELD_VALUE_CONVERTER_SET,
    ValueConverterRegistry,
)
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.field_policy import DEFAULT_FIELD_POLICY_SET
from pyrsql.core.joins import JoinHint
from pyrsql.core.options import QueryOptions, SortOptions
from pyrsql.core.procedure_policy import (
    DEFAULT_PROCEDURE_ACCESS_POLICY,
    ProcedureAccessPolicy,
)
from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS
from pyrsql.parsing.operators import (
    DEFAULT_OPERATOR_REGISTRY,
    ComparisonOperator,
    OperatorRegistry,
)
from pyrsql.sorting.limits import DEFAULT_SORT_LIMITS

if TYPE_CHECKING:
    from collections.abc import Mapping


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {"like_escape_character": "too-long"},
            r"escape",
            id="invalid-like-escape-character",
        ),
        pytest.param(
            {
                "custom_predicates": {
                    "wrong_name": CustomPredicateDefinition(
                        operator=ComparisonOperator(
                            name="all_match",
                            spellings=("=all=",),
                            minimum_arguments=1,
                            maximum_arguments=1,
                        ),
                        argument_type=str,
                    ),
                },
            },
            r"predicate",
            id="mismatched-custom-predicate-key",
        ),
    ],
)
def test_query_options_reject_invalid_public_configuration(
    kwargs: Mapping[str, object],
    pattern: str,
) -> None:
    """Rejects invalid escape and custom predicate configuration."""
    with pytest.raises(ValueError, match=pattern):
        QueryOptions(**cast("Any", kwargs))


def test_query_options_normalize_distinct_and_join_hints() -> None:
    """Normalizes simple query option containers into immutable values."""
    options = QueryOptions(
        distinct=True,
        join_hints={"User.company": JoinHint.LEFT},
    )

    assert options.distinct is True
    assert options.join_hints["User.company"] is JoinHint.LEFT


@pytest.mark.parametrize(
    ("options", "expected_model", "expected_name", "expected_value"),
    [
        pytest.param(
            QueryOptions(model_field_mapping={str: {"alias": "value"}}),
            str,
            "model_field_mapping",
            {"alias": "value"},
            id="query-model-field-mapping",
        ),
        pytest.param(
            QueryOptions(model_field_whitelist={str: frozenset({"value"})}),
            str,
            "model_field_whitelist",
            frozenset({"value"}),
            id="query-model-field-whitelist",
        ),
        pytest.param(
            QueryOptions(model_field_blacklist={int: frozenset({"blocked"})}),
            int,
            "model_field_blacklist",
            frozenset({"blocked"}),
            id="query-model-field-blacklist",
        ),
        pytest.param(
            SortOptions(model_field_mapping={str: {"alias": "value"}}),
            str,
            "model_field_mapping",
            {"alias": "value"},
            id="sort-model-field-mapping",
        ),
        pytest.param(
            SortOptions(model_field_whitelist={str: frozenset({"value"})}),
            str,
            "model_field_whitelist",
            frozenset({"value"}),
            id="sort-model-field-whitelist",
        ),
        pytest.param(
            SortOptions(model_field_blacklist={int: frozenset({"blocked"})}),
            int,
            "model_field_blacklist",
            frozenset({"blocked"}),
            id="sort-model-field-blacklist",
        ),
    ],
)
def test_options_normalize_model_scoped_policy_containers(
    options: QueryOptions | SortOptions,
    expected_model: type[object],
    expected_name: str,
    expected_value: object,
) -> None:
    """Normalizes model-scoped field policy containers."""
    normalized = getattr(options, expected_name)

    assert normalized[expected_model] == expected_value


def test_query_options_store_value_converter_registry() -> None:
    """Preserves the configured value conversion registry."""
    registry = ValueConverterRegistry({str: lambda raw: raw.upper()})
    options = QueryOptions(value_converter_registry=registry)

    assert options.value_converter_registry is registry


def test_query_options_store_field_value_converters() -> None:
    """Preserves normalized field-scoped converter configuration."""
    options = QueryOptions(
        field_value_converters={"created_at": lambda raw: raw},
        model_field_value_converters={str: {"value": lambda raw: raw}},
    )

    assert "created_at" in options.field_value_converters
    assert "value" in options.model_field_value_converters[str]


def test_query_options_cache_derived_policy_objects() -> None:
    """Caches derived helper objects after normalization."""
    options = QueryOptions()

    assert options.field_policy is options.field_policy
    assert options.field_converter_set is options.field_converter_set
    assert options.procedure_policy is options.procedure_policy
    assert options.field_policy.is_empty is True
    assert options.parse_limits is DEFAULT_PARSE_LIMITS
    assert options.field_policy is DEFAULT_FIELD_POLICY_SET
    assert options.procedure_policy is DEFAULT_PROCEDURE_ACCESS_POLICY
    assert options.field_converter_set is DEFAULT_FIELD_VALUE_CONVERTER_SET


@pytest.mark.parametrize(
    ("options", "expected_empty"),
    [
        pytest.param(
            QueryOptions(field_mapping={"alias": "name"}),
            False,
            id="query-policy-not-empty",
        ),
        pytest.param(
            SortOptions(model_field_whitelist={str: frozenset({"name"})}),
            False,
            id="sort-policy-not-empty",
        ),
    ],
)
def test_options_mark_field_policy_non_empty_when_restrictions_exist(
    options: QueryOptions | SortOptions,
    expected_empty: bool,
) -> None:
    """Marks derived field policy emptiness from configured restrictions."""
    assert options.field_policy.is_empty is expected_empty


def test_sort_options_are_normalized() -> None:
    """Normalizes simple sort option containers into immutable values."""
    options = SortOptions(
        field_whitelist=frozenset({"name"}),
        join_hints={"User.company": JoinHint.INNER},
    )

    assert options.field_whitelist == frozenset({"name"})
    assert options.join_hints["User.company"] is JoinHint.INNER


def test_sort_options_cache_derived_policy_objects() -> None:
    """Caches derived helper objects after normalization."""
    options = SortOptions()

    assert options.field_policy is options.field_policy
    assert options.procedure_policy is options.procedure_policy
    assert options.field_policy.is_empty is True
    assert options.sort_limits is DEFAULT_SORT_LIMITS
    assert options.field_policy is DEFAULT_FIELD_POLICY_SET
    assert options.procedure_policy is DEFAULT_PROCEDURE_ACCESS_POLICY


def test_procedure_policy_compiles_regex_rules() -> None:
    """Evaluates compiled whitelist and blacklist regex rules."""
    policy = ProcedureAccessPolicy.from_patterns(
        whitelist=("upper", "concat|lower"),
        blacklist=("lower",),
    )

    assert policy.is_whitelisted("upper") is True
    assert policy.is_whitelisted("concat") is True
    assert policy.is_whitelisted("trim") is False
    assert policy.is_blacklisted("lower") is True


def test_query_options_extend_operator_registry_with_custom_operator() -> None:
    """Extends operator registry through the configured options."""
    all_match = ComparisonOperator(
        name="all_match",
        spellings=("=all=",),
        minimum_arguments=1,
        maximum_arguments=1,
    )
    options = QueryOptions(
        operator_registry=OperatorRegistry(
            operators=DEFAULT_OPERATOR_REGISTRY.operators + (all_match,),
        ),
    )

    assert options.operator_registry.get("=all=").name == "all_match"
