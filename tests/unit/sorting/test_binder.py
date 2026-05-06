"""Unit tests for sort binding."""

import re
from collections.abc import Mapping
import pytest

from pyrsql.ir.query import BoundField, BoundFunction
from pyrsql.sorting.binder import SortBinder
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
)
from pyrsql.sorting.parser import SortParser


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
    selector = bound_sort.fields[0].selector
    assert isinstance(selector, BoundField)
    assert selector.raw_path == "companyName"
    assert selector.field_path == "company.name"


def test_sort_binder_enforces_whitelist() -> None:
    """Rejects sort fields outside the configured whitelist."""
    fields = SortParser("name").parse()
    with pytest.raises(SortFieldNotWhitelistedError):
        SortBinder(_SortOptions(field_whitelist=frozenset({"city"}))).bind(
            fields
        )


def test_sort_binder_enforces_blacklist() -> None:
    """Rejects sort fields inside the configured blacklist."""
    fields = SortParser("name").parse()
    with pytest.raises(SortFieldBlacklistedError):
        SortBinder(_SortOptions(field_blacklist=frozenset({"name"}))).bind(
            fields
        )


def test_sort_binder_maps_field_selectors_inside_functions() -> None:
    """Applies field mapping recursively inside function selectors."""
    fields = SortParser("@upper[companyName],asc").parse()
    bound_sort = SortBinder(
        _SortOptions(
            field_mapping={"companyName": "company.name"},
            procedure_whitelist=("upper",),
        )
    ).bind(fields)
    selector = bound_sort.fields[0].selector
    assert isinstance(selector, BoundFunction)
    assert isinstance(selector.arguments[0], BoundField)
    assert selector.arguments[0].field_path == "company.name"


def test_sort_binder_rejects_non_whitelisted_functions() -> None:
    """Rejects function selectors that are not in the whitelist."""
    fields = SortParser("@upper[name],asc").parse()
    with pytest.raises(SortFunctionNotWhitelistedError):
        SortBinder(_SortOptions()).bind(fields)


def test_sort_binder_rejects_blacklisted_functions() -> None:
    """Rejects function selectors that are blacklisted."""
    fields = SortParser("@upper[@lower[name]],asc").parse()
    with pytest.raises(SortFunctionBlacklistedError):
        SortBinder(
            _SortOptions(
                procedure_whitelist=(".*er",),
                procedure_blacklist=("lower",),
            )
        ).bind(fields)
