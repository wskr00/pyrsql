"""Sanity tests for the backend-neutral public API."""

import pytest

import pyrsql
from pyrsql.backends.sqlalchemy import SQLAlchemyBackend
from pyrsql.core.conversion import ValueConverterRegistry
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.joins import JoinHint
from pyrsql.core.options import QueryOptions
from pyrsql.core.options import SortOptions
from pyrsql.core.page import PageRequest
from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.operators import OperatorRegistry
from pyrsql.core.sort import Sort


def test_parse_returns_query_object() -> None:
    """Ensures the package-level parse helper builds a query object."""
    query = pyrsql.parse("name==demo")
    assert query.text == "name==demo"
    assert query.options.strict_equality is False
    assert query.expression is not None
    assert query.semantic_expression is not None


def test_parse_uses_custom_operator_registry() -> None:
    """Ensures package parsing honors custom operator configuration."""
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
    query = pyrsql.parse("name=all=demo", options=options)
    assert query.expression is not None
    assert query.expression.operator.name == "all_match"


def test_parse_uses_custom_predicate_definition() -> None:
    """Ensures custom predicates extend the operator registry automatically."""
    all_match = ComparisonOperator(
        name="all_match",
        spellings=("=all=",),
        minimum_arguments=1,
        maximum_arguments=1,
    )
    options = QueryOptions(
        custom_predicates={
            "all_match": CustomPredicateDefinition(
                operator=all_match,
                argument_type=str,
            )
        }
    )
    query = pyrsql.parse("name=all=demo", options=options)
    assert query.expression is not None
    assert query.expression.operator.name == "all_match"


def test_compile_uses_backend_name() -> None:
    """Ensures compilation returns the selected backend metadata."""
    compilation = pyrsql.compile(
        "name==demo",
        backend=SQLAlchemyBackend(),
    )
    assert compilation.backend_name == "sqlalchemy"


def test_query_options_validate_like_escape_character() -> None:
    """Rejects invalid escape-character configuration."""
    with pytest.raises(ValueError):
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


def test_query_options_reject_mismatched_custom_predicate_key() -> None:
    """Rejects custom predicate definitions keyed by the wrong name."""
    with pytest.raises(ValueError):
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


def test_sort_parse_returns_sort_object() -> None:
    """Ensures the Sort type builds a sort object from raw text."""
    sort = Sort.parse("name,desc")
    assert sort.text == "name,desc"
    assert len(sort.fields) == 1
    assert len(sort.semantic_fields) == 1


def test_sort_compile_uses_backend_name() -> None:
    """Ensures sort compilation returns the selected backend metadata."""
    compilation = Sort.parse("name,asc").compile(
        backend=SQLAlchemyBackend(),
    )
    assert compilation.backend_name == "sqlalchemy"


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


def test_page_request_apply_uses_backend() -> None:
    """Ensures page requests apply through the selected backend."""
    compilation = PageRequest.of(0, 10).compile(backend=SQLAlchemyBackend())
    assert compilation.backend_name == "sqlalchemy"
