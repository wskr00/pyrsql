"""Unit tests for sort binding."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from pyrsql.selector.ast import FieldSelector, FunctionSelector
from pyrsql.sorting.binder import SortBinder
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
)
from pyrsql.sorting.parser import SortParser

if TYPE_CHECKING:
    from collections.abc import Mapping


class _ProcedurePolicy:
    """Minimal procedure policy for sorting module tests."""

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


class _SortOptions:
    """Minimal options object for sorting module tests."""

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


def test_sort_binder_applies_field_mapping() -> None:
    """Resolves aliased sort selectors into canonical field paths."""
    fields = SortParser("companyName,desc").parse()
    options = _SortOptions(field_mapping={"companyName": "company.name"})
    bound_sort = SortBinder(options).bind(fields)
    selector = bound_sort[0].selector

    assert isinstance(selector, FieldSelector)
    assert selector.raw_path == "company.name"


@pytest.mark.parametrize(
    ("options", "expected_error"),
    [
        pytest.param(
            _SortOptions(field_whitelist=frozenset({"city"})),
            SortFieldNotWhitelistedError,
            id="field-whitelist",
        ),
        pytest.param(
            _SortOptions(field_blacklist=frozenset({"name"})),
            SortFieldBlacklistedError,
            id="field-blacklist",
        ),
    ],
)
def test_sort_binder_enforces_field_policies(
    options: _SortOptions,
    expected_error: type[Exception],
) -> None:
    """Rejects fields that violate whitelist or blacklist rules."""
    fields = SortParser("name").parse()

    with pytest.raises(expected_error):
        SortBinder(options).bind(fields)


def test_sort_binder_maps_field_selectors_inside_functions() -> None:
    """Applies field mapping recursively inside function selectors."""
    fields = SortParser("@upper[companyName],asc").parse()
    bound_sort = SortBinder(
        _SortOptions(
            field_mapping={"companyName": "company.name"},
            procedure_whitelist=("upper",),
        ),
    ).bind(fields)
    selector = bound_sort[0].selector

    assert isinstance(selector, FunctionSelector)
    assert isinstance(selector.arguments[0], FieldSelector)
    assert selector.arguments[0].raw_path == "company.name"


@pytest.mark.parametrize(
    ("source", "options", "expected_error"),
    [
        pytest.param(
            "@upper[name],asc",
            _SortOptions(),
            SortFunctionNotWhitelistedError,
            id="function-not-whitelisted",
        ),
        pytest.param(
            "@upper[@lower[name]],asc",
            _SortOptions(
                procedure_whitelist=(".*er",),
                procedure_blacklist=("lower",),
            ),
            SortFunctionBlacklistedError,
            id="function-blacklisted",
        ),
    ],
)
def test_sort_binder_enforces_function_policies(
    source: str,
    options: _SortOptions,
    expected_error: type[Exception],
) -> None:
    """Rejects functions that violate whitelist or blacklist rules."""
    fields = SortParser(source).parse()

    with pytest.raises(expected_error):
        SortBinder(options).bind(fields)


def test_sort_binder_prefers_blacklist_over_whitelist_for_fields() -> None:
    """Explicit field blacklist takes precedence over whitelist membership."""
    fields = SortParser("name").parse()
    options = _SortOptions(
        field_whitelist=frozenset({"name"}),
        field_blacklist=frozenset({"name"}),
    )

    with pytest.raises(SortFieldBlacklistedError, match=r"blocked"):
        SortBinder(options).bind(fields)


def test_sort_binder_prefers_blacklist_over_whitelist_for_functions() -> None:
    """Explicit function blacklist takes precedence over whitelist matches."""
    fields = SortParser("@upper[name],asc").parse()
    options = _SortOptions(
        procedure_whitelist=("upper",),
        procedure_blacklist=("upper",),
    )

    with pytest.raises(SortFunctionBlacklistedError, match=r"blacklisted"):
        SortBinder(options).bind(fields)
