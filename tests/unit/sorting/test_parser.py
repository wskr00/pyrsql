"""Unit tests for the pyrsql sort parser."""

from __future__ import annotations

import pytest

from pyrsql.selector.ast import FieldSelector, FunctionSelector, LiteralSelector
from pyrsql.sorting.ast import SortDirection
from pyrsql.sorting.errors import SortParseError
from pyrsql.sorting.limits import SortLimits
from pyrsql.sorting.parser import SortParser


@pytest.mark.parametrize(
    ("source", "expected_path", "expected_direction", "expected_ignore_case"),
    [
        pytest.param(
            "name",
            "name",
            SortDirection.ASCENDING,
            False,
            id="default-ascending",
        ),
        pytest.param(
            "company.name,desc,ic",
            "company.name",
            SortDirection.DESCENDING,
            True,
            id="direction-and-ignore-case",
        ),
        pytest.param(
            " company.name , desc , ic ",
            "company.name",
            SortDirection.DESCENDING,
            True,
            id="trimmed-clause-parts",
        ),
    ],
)
def test_sort_parser_builds_field_selectors(
    source: str,
    expected_path: str,
    expected_direction: SortDirection,
    expected_ignore_case: bool,
) -> None:
    """Parses plain sort field selectors with normalized modifiers."""
    fields = SortParser(source).parse()

    assert len(fields) == 1
    assert isinstance(fields[0].selector, FieldSelector)
    assert fields[0].selector.raw_path == expected_path
    assert fields[0].direction is expected_direction
    assert fields[0].ignore_case is expected_ignore_case


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(";;name,asc;;", id="empty-clauses"),
        pytest.param(" ; ; name,asc ; ", id="whitespace-only-clauses"),
    ],
)
def test_sort_parser_ignores_empty_clauses(source: str) -> None:
    """Ignores empty semicolon-delimited clauses."""
    fields = SortParser(source).parse()

    assert len(fields) == 1
    assert isinstance(fields[0].selector, FieldSelector)
    assert fields[0].selector.raw_path == "name"


def test_sort_parser_supports_function_selectors() -> None:
    """Parses nested function selectors with literal arguments."""
    fields = SortParser("@concat[@upper[name]|#123],asc").parse()
    selector = fields[0].selector

    assert len(fields) == 1
    assert isinstance(selector, FunctionSelector)
    assert selector.function_name == "concat"
    assert isinstance(selector.arguments[0], FunctionSelector)
    assert isinstance(selector.arguments[1], LiteralSelector)
    assert selector.arguments[1].value == 123


@pytest.mark.parametrize(
    ("source", "limits", "pattern"),
    [
        pytest.param(
            "name,sideways",
            None,
            r"unsupported direction",
            id="invalid-direction",
        ),
        pytest.param(
            "name,asc,raw",
            None,
            r"unsupported modifier",
            id="invalid-modifier",
        ),
        pytest.param(
            "name;city",
            SortLimits(max_fields=1),
            r"maximum supported field count",
            id="field-count-limit",
        ),
        pytest.param(
            "company.name,desc",
            SortLimits(max_sort_length=5),
            r"maximum supported length",
            id="total-length-limit",
        ),
    ],
)
def test_sort_parser_rejects_invalid_input(
    source: str,
    limits: SortLimits | None,
    pattern: str,
) -> None:
    """Rejects unsupported tokens and configured parser limit violations."""
    with pytest.raises(SortParseError, match=pattern):
        SortParser(source, limits=limits).parse()


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
