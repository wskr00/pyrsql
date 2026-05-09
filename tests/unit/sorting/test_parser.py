"""Unit tests for the pyrsql sort parser."""

import pytest

from pyrsql.selector.ast import (
    FieldSelector,
    FunctionSelector,
    LiteralSelector,
)
from pyrsql.sorting.ast import SortDirection
from pyrsql.sorting.errors import SortParseError
from pyrsql.sorting.limits import SortLimits
from pyrsql.sorting.parser import SortParser


def test_sort_parser_supports_default_ascending_direction() -> None:
    """Parses a single selector with default ascending direction."""
    fields = SortParser("name").parse()
    assert len(fields) == 1
    assert isinstance(fields[0].selector, FieldSelector)
    assert fields[0].selector.raw_path == "name"
    assert fields[0].direction is SortDirection.ASCENDING
    assert fields[0].ignore_case is False


def test_sort_parser_supports_direction_and_ignore_case() -> None:
    """Parses direction and ignore-case modifier."""
    fields = SortParser("company.name,desc,ic").parse()
    assert len(fields) == 1
    assert fields[0].direction is SortDirection.DESCENDING
    assert fields[0].ignore_case is True


def test_sort_parser_trims_clause_parts() -> None:
    """Parses clause parts with surrounding whitespace."""
    fields = SortParser(" company.name , desc , ic ").parse()
    assert len(fields) == 1
    assert isinstance(fields[0].selector, FieldSelector)
    assert fields[0].selector.raw_path == "company.name"
    assert fields[0].direction is SortDirection.DESCENDING
    assert fields[0].ignore_case is True


def test_sort_parser_ignores_empty_clauses() -> None:
    """Ignores empty semicolon-delimited clauses."""
    fields = SortParser(";;name,asc;;").parse()
    assert len(fields) == 1
    assert isinstance(fields[0].selector, FieldSelector)
    assert fields[0].selector.raw_path == "name"


def test_sort_parser_ignores_whitespace_only_clauses() -> None:
    """Ignores semicolon-delimited clauses that only contain whitespace."""
    fields = SortParser(" ; ; name,asc ; ").parse()
    assert len(fields) == 1
    assert isinstance(fields[0].selector, FieldSelector)
    assert fields[0].selector.raw_path == "name"


def test_sort_parser_supports_function_selectors() -> None:
    """Parses nested function selectors with literal arguments."""
    fields = SortParser("@concat[@upper[name]|#123],asc").parse()
    assert len(fields) == 1
    selector = fields[0].selector
    assert isinstance(selector, FunctionSelector)
    assert selector.function_name == "concat"
    assert isinstance(selector.arguments[0], FunctionSelector)
    assert isinstance(selector.arguments[1], LiteralSelector)
    assert selector.arguments[1].value == 123


def test_sort_parser_rejects_invalid_direction() -> None:
    """Rejects unsupported direction tokens."""
    with pytest.raises(SortParseError):
        SortParser("name,sideways").parse()


def test_sort_parser_rejects_invalid_modifier() -> None:
    """Rejects unsupported sort modifiers."""
    with pytest.raises(SortParseError):
        SortParser("name,asc,raw").parse()


def test_sort_parser_enforces_field_count_limit() -> None:
    """Rejects sort expressions that exceed the configured field limit."""
    with pytest.raises(SortParseError):
        SortParser(
            "name;city",
            limits=SortLimits(max_fields=1),
        ).parse()


def test_sort_parser_enforces_total_length_limit() -> None:
    """Rejects sort expressions that exceed the configured length limit."""
    with pytest.raises(SortParseError):
        SortParser(
            "company.name,desc",
            limits=SortLimits(max_sort_length=5),
        ).parse()


def test_sort_limits_reject_invalid_values() -> None:
    """Rejects invalid sort parser safety limits."""
    with pytest.raises(ValueError, match="max_sort_length"):
        SortLimits(max_sort_length=0)


def test_sort_parse_error_exposes_structured_diagnostic() -> None:
    """Exposes a structured diagnostic on sort parsing failures."""
    with pytest.raises(SortParseError) as exc_info:
        SortParser("name,sideways").parse()
    assert exc_info.value.code == "sort_parse_error"
    assert exc_info.value.diagnostic.code == "sort_parse_error"
