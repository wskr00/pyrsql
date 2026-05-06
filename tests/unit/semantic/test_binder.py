"""Unit tests for semantic binding."""

from collections.abc import Mapping

import pytest

from pyrsql.ir.query import BoundComparison, BoundField, BoundFunction, BoundLogical
from pyrsql.parsing.ast import Expression
from pyrsql.parsing.limits import ParseLimits
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.parser import Parser
from pyrsql.core.procedure_policy import ProcedureAccessPolicy
from pyrsql.semantic.binder import SemanticBinder
from pyrsql.semantic.errors import (
    FieldBlacklistedError,
    FieldNotWhitelistedError,
    FunctionBlacklistedError,
    FunctionNotWhitelistedError,
)


class _SemanticOptions:
    """Minimal options object for semantic module tests."""

    def __init__(
        self,
        *,
        field_mapping: Mapping[str, str] | None = None,
        field_whitelist: frozenset[str] = frozenset(),
        field_blacklist: frozenset[str] = frozenset(),
        procedure_whitelist: tuple[str, ...] = (),
        procedure_blacklist: tuple[str, ...] = (),
    ) -> None:
        self.field_mapping = field_mapping or {}
        self.field_whitelist = field_whitelist
        self.field_blacklist = field_blacklist
        self.procedure_policy = ProcedureAccessPolicy.from_patterns(
            procedure_whitelist,
            procedure_blacklist,
        )


def _parse(query_text: str) -> Expression:
    return Parser(
        query_text,
        limits=ParseLimits(),
        operator_registry=DEFAULT_OPERATOR_REGISTRY,
    ).parse()


def test_semantic_binder_applies_field_mapping() -> None:
    """Resolves aliased selectors into canonical field paths."""
    expression = _parse("username==demo")
    options = _SemanticOptions(field_mapping={"username": "user.name"})
    bound_expression = SemanticBinder(options).bind(expression)
    assert isinstance(bound_expression, BoundComparison)
    assert isinstance(bound_expression.selector, BoundField)
    assert bound_expression.selector.raw_path == "username"
    assert bound_expression.selector.field_path == "user.name"


def test_semantic_binder_preserves_logical_shape() -> None:
    """Keeps logical nodes while binding child comparisons."""
    expression = _parse("username==demo;city==sp")
    options = _SemanticOptions(field_mapping={"username": "user.name"})
    bound_expression = SemanticBinder(options).bind(expression)
    assert isinstance(bound_expression, BoundLogical)
    first_child = bound_expression.children[0]
    assert isinstance(first_child, BoundComparison)
    assert isinstance(first_child.selector, BoundField)
    assert first_child.selector.field_path == "user.name"


def test_semantic_binder_enforces_whitelist() -> None:
    """Rejects fields outside the configured whitelist."""
    expression = _parse("name==demo")
    options = _SemanticOptions(field_whitelist=frozenset({"city"}))
    with pytest.raises(FieldNotWhitelistedError, match="not allowed"):
        SemanticBinder(options).bind(expression)


def test_semantic_binder_enforces_blacklist() -> None:
    """Rejects fields inside the configured blacklist."""
    expression = _parse("name==demo")
    options = _SemanticOptions(field_blacklist=frozenset({"name"}))
    with pytest.raises(FieldBlacklistedError, match="blocked"):
        SemanticBinder(options).bind(expression)


def test_semantic_binder_maps_field_selectors_inside_functions() -> None:
    """Applies field mapping recursively inside function selectors."""
    expression = _parse("@upper[username]==demo")
    options = _SemanticOptions(
        field_mapping={"username": "user.name"},
        procedure_whitelist=("upper",),
    )
    bound_expression = SemanticBinder(options).bind(expression)
    assert isinstance(bound_expression, BoundComparison)
    assert isinstance(bound_expression.selector, BoundFunction)
    assert isinstance(bound_expression.selector.arguments[0], BoundField)
    assert bound_expression.selector.arguments[0].field_path == "user.name"


def test_semantic_binder_rejects_non_whitelisted_functions() -> None:
    """Rejects function selectors outside the configured whitelist."""
    expression = _parse("@upper[name]==demo")
    with pytest.raises(FunctionNotWhitelistedError):
        SemanticBinder(_SemanticOptions()).bind(expression)


def test_semantic_binder_rejects_blacklisted_functions() -> None:
    """Rejects function selectors inside the configured blacklist."""
    expression = _parse("@upper[@lower[name]]==demo")
    with pytest.raises(FunctionBlacklistedError):
        SemanticBinder(
            _SemanticOptions(
                procedure_whitelist=(".*er",),
                procedure_blacklist=("lower",),
            )
        ).bind(expression)


def test_semantic_errors_expose_structured_diagnostic() -> None:
    """Exposes structured diagnostics from semantic errors."""
    expression = _parse("@upper[name]==demo")
    with pytest.raises(FunctionNotWhitelistedError) as exc_info:
        SemanticBinder(_SemanticOptions()).bind(expression)
    assert exc_info.value.code == "function_not_whitelisted"
    assert exc_info.value.diagnostic.code == "function_not_whitelisted"
