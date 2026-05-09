"""Unit tests for orm-neutral core options and policies."""

import pytest

from pyrsql.core.conversion import ValueConverterRegistry
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


def test_query_options_validate_like_escape_character() -> None:
    """Rejects invalid escape-character configuration."""
    with pytest.raises(ValueError, match="(?i)escape"):
        QueryOptions(like_escape_character="too-long")


def test_query_options_normalize_distinct_and_join_hints() -> None:
    """Normalizes query option containers into immutable values."""
    options = QueryOptions(
        distinct=True,
        join_hints={"User.company": JoinHint.LEFT},
    )
    assert options.distinct is True
    assert options.join_hints["User.company"] is JoinHint.LEFT


def test_query_options_normalize_model_field_policies() -> None:
    """Normalizes model-scoped field mapping and ACL containers."""
    options = QueryOptions(
        model_field_mapping={str: {"alias": "value"}},
        model_field_whitelist={str: frozenset({"value"})},
        model_field_blacklist={int: frozenset({"blocked"})},
    )
    assert options.model_field_mapping[str]["alias"] == "value"
    assert options.model_field_whitelist[str] == frozenset({"value"})
    assert options.model_field_blacklist[int] == frozenset({"blocked"})


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


def test_query_options_reject_mismatched_custom_predicate_key() -> None:
    """Rejects custom predicate definitions keyed by the wrong name."""
    with pytest.raises(ValueError, match="(?i)predicate"):
        QueryOptions(
            custom_predicates={
                "wrong_name": CustomPredicateDefinition(
                    operator=ComparisonOperator(
                        name="all_match",
                        spellings=("=all=",),
                        minimum_arguments=1,
                        maximum_arguments=1,
                    ),
                    argument_type=str,
                )
            }
        )


def test_sort_options_are_normalized() -> None:
    """Normalizes sort option containers into immutable values."""
    options = SortOptions(
        field_whitelist=frozenset({"name"}),
        join_hints={"User.company": JoinHint.INNER},
    )
    assert options.field_whitelist == frozenset({"name"})
    assert options.join_hints["User.company"] is JoinHint.INNER


def test_sort_options_normalize_model_field_policies() -> None:
    """Normalizes model-scoped sort policy containers."""
    options = SortOptions(
        model_field_mapping={str: {"alias": "value"}},
        model_field_whitelist={str: frozenset({"value"})},
        model_field_blacklist={int: frozenset({"blocked"})},
    )
    assert options.model_field_mapping[str]["alias"] == "value"
    assert options.model_field_whitelist[str] == frozenset({"value"})
    assert options.model_field_blacklist[int] == frozenset({"blocked"})


def test_sort_options_cache_derived_policy_objects() -> None:
    """Caches derived helper objects after normalization."""
    options = SortOptions()
    assert options.field_policy is options.field_policy
    assert options.procedure_policy is options.procedure_policy
    assert options.field_policy.is_empty is True
    assert options.sort_limits is DEFAULT_SORT_LIMITS
    assert options.field_policy is DEFAULT_FIELD_POLICY_SET
    assert options.procedure_policy is DEFAULT_PROCEDURE_ACCESS_POLICY


def test_query_options_field_policy_is_not_empty_when_restrictions_exist() -> (
    None
):
    """Marks field policy as non-empty for configured query restrictions."""
    options = QueryOptions(field_mapping={"alias": "name"})
    assert options.field_policy.is_empty is False


def test_sort_options_field_policy_is_not_empty_when_restrictions_exist() -> (
    None
):
    """Marks field policy as non-empty when sort restrictions are configured."""
    options = SortOptions(model_field_whitelist={str: frozenset({"name"})})
    assert options.field_policy.is_empty is False


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
            operators=DEFAULT_OPERATOR_REGISTRY.operators + (all_match,)
        )
    )
    assert options.operator_registry.get("=all=").name == "all_match"
