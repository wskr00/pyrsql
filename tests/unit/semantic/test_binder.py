"""Unit tests for semantic binding."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from pyrsql.ir.query import (
    BoundComparison,
    BoundField,
    BoundFunction,
    BoundLogical,
)
from pyrsql.parsing.parser import Parser
from pyrsql.semantic.binder import SemanticBinder
from pyrsql.semantic.errors import (
    FieldBlacklistedError,
    FieldNotWhitelistedError,
    FunctionBlacklistedError,
    FunctionNotWhitelistedError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyrsql.parsing.ast import Expression


class _ProcedurePolicy:
    """Minimal procedure policy for semantic module tests."""

    def __init__(
        self,
        *,
        whitelist: tuple[str, ...] = (),
        blacklist: tuple[str, ...] = (),
    ) -> None:
        self._whitelist = tuple(re.compile(pattern) for pattern in whitelist)
        self._blacklist = tuple(re.compile(pattern) for pattern in blacklist)

    def is_whitelisted(self, function_name: str) -> bool:
        """Returns whether a function is allowed."""
        if not self._whitelist:
            return False
        return any(
            pattern.fullmatch(function_name) is not None
            for pattern in self._whitelist
        )

    def is_blacklisted(self, function_name: str) -> bool:
        """Returns whether a function is blocked."""
        return any(
            pattern.fullmatch(function_name) is not None
            for pattern in self._blacklist
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
        self.procedure_policy = _ProcedurePolicy(
            whitelist=procedure_whitelist,
            blacklist=procedure_blacklist,
        )


def _parse(query_text: str) -> Expression:
    """Parses one semantic test expression through the public parser."""
    return Parser(query_text).parse()


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


@pytest.mark.parametrize(
    ("options", "expected_error"),
    [
        pytest.param(
            _SemanticOptions(field_whitelist=frozenset({"city"})),
            FieldNotWhitelistedError,
            id="field-whitelist",
        ),
        pytest.param(
            _SemanticOptions(field_blacklist=frozenset({"name"})),
            FieldBlacklistedError,
            id="field-blacklist",
        ),
    ],
)
def test_semantic_binder_enforces_field_policies(
    options: _SemanticOptions,
    expected_error: type[Exception],
) -> None:
    """Rejects fields that violate whitelist or blacklist rules."""
    expression = _parse("name==demo")

    with pytest.raises(expected_error, match=r"not allowed|blocked"):
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


@pytest.mark.parametrize(
    ("source", "options", "expected_error"),
    [
        pytest.param(
            "@upper[name]==demo",
            _SemanticOptions(),
            FunctionNotWhitelistedError,
            id="function-not-whitelisted",
        ),
        pytest.param(
            "@upper[@lower[name]]==demo",
            _SemanticOptions(
                procedure_whitelist=(".*er",),
                procedure_blacklist=("lower",),
            ),
            FunctionBlacklistedError,
            id="function-blacklisted",
        ),
    ],
)
def test_semantic_binder_enforces_function_policies(
    source: str,
    options: _SemanticOptions,
    expected_error: type[Exception],
) -> None:
    """Rejects functions that violate whitelist or blacklist rules."""
    expression = _parse(source)

    with pytest.raises(expected_error):
        SemanticBinder(options).bind(expression)


def test_semantic_binder_prefers_blacklist_over_whitelist_for_fields() -> None:
    """Explicit field blacklist takes precedence over whitelist membership."""
    expression = _parse("name==demo")
    options = _SemanticOptions(
        field_whitelist=frozenset({"name"}),
        field_blacklist=frozenset({"name"}),
    )

    with pytest.raises(FieldBlacklistedError, match=r"blocked"):
        SemanticBinder(options).bind(expression)


def test_semantic_binder_prefers_blacklist_over_whitelist_for_functions() -> (
    None
):
    """Explicit function blacklist takes precedence over whitelist matches."""
    expression = _parse("@upper[name]==demo")
    options = _SemanticOptions(
        procedure_whitelist=("upper",),
        procedure_blacklist=("upper",),
    )

    with pytest.raises(FunctionBlacklistedError, match=r"blacklisted"):
        SemanticBinder(options).bind(expression)


def test_semantic_errors_expose_structured_diagnostic() -> None:
    """Exposes structured diagnostics from semantic errors."""
    expression = _parse("@upper[name]==demo")

    with pytest.raises(FunctionNotWhitelistedError) as exc_info:
        SemanticBinder(_SemanticOptions()).bind(expression)

    assert exc_info.value.code == "function_not_whitelisted"
    assert exc_info.value.diagnostic.code == "function_not_whitelisted"
