"""Unit tests for sort semantic analysis."""

import pytest

from pyrsql.core.options import SortOptions
from pyrsql.selector.semantic import (
    SemanticColumnSelector,
    SemanticFunctionSelector,
)
from pyrsql.sorting.analyzer import SortAnalyzer
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
)
from pyrsql.sorting.parser import SortParser


def test_sort_analyzer_applies_field_mapping() -> None:
    """Resolves aliased sort selectors into canonical field paths."""
    fields = SortParser("companyName,desc").parse()
    options = SortOptions(field_mapping={"companyName": "company.name"})
    semantic_fields = SortAnalyzer(options).analyze(fields)
    selector = semantic_fields[0].selector
    assert isinstance(selector, SemanticColumnSelector)
    assert selector.selector == "companyName"
    assert selector.field_path == "company.name"


def test_sort_analyzer_enforces_whitelist() -> None:
    """Rejects sort fields outside the configured whitelist."""
    fields = SortParser("name").parse()
    with pytest.raises(SortFieldNotWhitelistedError):
        SortAnalyzer(SortOptions(field_whitelist=frozenset({"city"}))).analyze(
            fields
        )


def test_sort_analyzer_enforces_blacklist() -> None:
    """Rejects sort fields inside the configured blacklist."""
    fields = SortParser("name").parse()
    with pytest.raises(SortFieldBlacklistedError):
        SortAnalyzer(SortOptions(field_blacklist=frozenset({"name"}))).analyze(
            fields
        )


def test_sort_analyzer_maps_field_selectors_inside_functions() -> None:
    """Applies field mapping recursively inside function selectors."""
    fields = SortParser("@upper[companyName],asc").parse()
    semantic_fields = SortAnalyzer(
        SortOptions(
            field_mapping={"companyName": "company.name"},
            procedure_whitelist=("upper",),
        )
    ).analyze(fields)
    selector = semantic_fields[0].selector
    assert isinstance(selector, SemanticFunctionSelector)
    assert isinstance(selector.arguments[0], SemanticColumnSelector)
    assert selector.arguments[0].field_path == "company.name"


def test_sort_analyzer_rejects_non_whitelisted_functions() -> None:
    """Rejects function selectors that are not in the whitelist."""
    fields = SortParser("@upper[name],asc").parse()
    with pytest.raises(SortFunctionNotWhitelistedError):
        SortAnalyzer(SortOptions()).analyze(fields)


def test_sort_analyzer_rejects_blacklisted_functions() -> None:
    """Rejects function selectors that are blacklisted."""
    fields = SortParser("@upper[@lower[name]],asc").parse()
    with pytest.raises(SortFunctionBlacklistedError):
        SortAnalyzer(
            SortOptions(
                procedure_whitelist=(".*er",),
                procedure_blacklist=("lower",),
            )
        ).analyze(fields)
