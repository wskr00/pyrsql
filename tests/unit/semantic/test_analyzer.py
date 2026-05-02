"""Unit tests for semantic analysis."""

import pytest

from pyrsql.core.options import QueryOptions
from pyrsql.parsing.parser import Parser
from pyrsql.selector.semantic import (
    SemanticColumnSelector,
    SemanticFunctionSelector,
)
from pyrsql.semantic.analyzer import SemanticAnalyzer
from pyrsql.semantic.ast import SemanticComparison, SemanticLogical
from pyrsql.semantic.errors import (
    FieldBlacklistedError,
    FieldNotWhitelistedError,
    FunctionBlacklistedError,
    FunctionNotWhitelistedError,
)


def test_semantic_analyzer_applies_field_mapping() -> None:
    """Resolves aliased selectors into canonical field paths."""
    expression = Parser("username==demo").parse()
    options = QueryOptions(field_mapping={"username": "user.name"})
    semantic_expression = SemanticAnalyzer(options).analyze(expression)
    assert isinstance(semantic_expression, SemanticComparison)
    assert isinstance(semantic_expression.selector, SemanticColumnSelector)
    assert semantic_expression.selector.selector == "username"
    assert semantic_expression.selector.field_path == "user.name"


def test_semantic_analyzer_preserves_logical_shape() -> None:
    """Keeps logical nodes while normalizing child comparisons."""
    expression = Parser("username==demo;city==sp").parse()
    options = QueryOptions(field_mapping={"username": "user.name"})
    semantic_expression = SemanticAnalyzer(options).analyze(expression)
    assert isinstance(semantic_expression, SemanticLogical)
    first_child = semantic_expression.children[0]
    assert isinstance(first_child, SemanticComparison)
    assert isinstance(first_child.selector, SemanticColumnSelector)
    assert first_child.selector.field_path == "user.name"


def test_semantic_analyzer_enforces_whitelist() -> None:
    """Rejects fields outside the configured whitelist."""
    expression = Parser("name==demo").parse()
    options = QueryOptions(field_whitelist=frozenset({"city"}))
    try:
        SemanticAnalyzer(options).analyze(expression)
    except FieldNotWhitelistedError as error:
        assert "not allowed" in str(error)
    else:
        raise AssertionError("Expected a FieldNotWhitelistedError.")


def test_semantic_analyzer_enforces_blacklist() -> None:
    """Rejects fields inside the configured blacklist."""
    expression = Parser("name==demo").parse()
    options = QueryOptions(field_blacklist=frozenset({"name"}))
    try:
        SemanticAnalyzer(options).analyze(expression)
    except FieldBlacklistedError as error:
        assert "blocked" in str(error)
    else:
        raise AssertionError("Expected a FieldBlacklistedError.")


def test_semantic_analyzer_maps_field_selectors_inside_functions() -> None:
    """Applies field mapping recursively inside function selectors."""
    expression = Parser("@upper[username]==demo").parse()
    options = QueryOptions(
        field_mapping={"username": "user.name"},
        procedure_whitelist=("upper",),
    )
    semantic_expression = SemanticAnalyzer(options).analyze(expression)
    assert isinstance(semantic_expression, SemanticComparison)
    assert isinstance(semantic_expression.selector, SemanticFunctionSelector)
    assert isinstance(
        semantic_expression.selector.arguments[0],
        SemanticColumnSelector,
    )
    assert semantic_expression.selector.arguments[0].field_path == "user.name"


def test_semantic_analyzer_rejects_non_whitelisted_functions() -> None:
    """Rejects function selectors outside the configured whitelist."""
    expression = Parser("@upper[name]==demo").parse()
    with pytest.raises(FunctionNotWhitelistedError):
        SemanticAnalyzer(QueryOptions()).analyze(expression)


def test_semantic_analyzer_rejects_blacklisted_functions() -> None:
    """Rejects function selectors inside the configured blacklist."""
    expression = Parser("@upper[@lower[name]]==demo").parse()
    with pytest.raises(FunctionBlacklistedError):
        SemanticAnalyzer(
            QueryOptions(
                procedure_whitelist=(".*er",),
                procedure_blacklist=("lower",),
            )
        ).analyze(expression)
