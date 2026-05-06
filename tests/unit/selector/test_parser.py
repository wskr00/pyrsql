"""Unit tests for the shared selector parser."""

import pytest

from pyrsql.selector.ast import FieldSelector, FunctionSelector, LiteralSelector
from pyrsql.selector.parser import SelectorParseError, SelectorParser


def test_split_top_level_trims_and_discards_blank_fragments() -> None:
    """Splits top-level fragments into normalized non-empty parts."""
    parser = SelectorParser()
    fragments = parser.split_top_level(
        "  name  | @upper[ city ] |   | #123  ",
        delimiter="|",
    )
    assert fragments == ("name", "@upper[ city ]", "#123")


def test_parse_field_selector_preserves_segments() -> None:
    """Parses field selectors into raw path and path segments."""
    selector = SelectorParser().parse(
        "company.name",
        max_length=100,
        context="selector",
    )
    assert isinstance(selector, FieldSelector)
    assert selector.raw_path == "company.name"
    assert selector.segments == ("company", "name")


def test_parse_literal_selector_keeps_literal_value() -> None:
    """Parses literal selectors into typed literal nodes."""
    selector = SelectorParser().parse(
        "#true",
        max_length=100,
        context="selector",
    )
    assert isinstance(selector, LiteralSelector)
    assert selector.value is True


def test_parse_function_selector_walks_nested_arguments() -> None:
    """Parses nested function selectors into a traversable syntax tree."""
    selector = SelectorParser().parse(
        "@upper[name|#1]",
        max_length=100,
        context="selector",
    )
    assert isinstance(selector, FunctionSelector)
    walked = tuple(selector.walk())
    assert isinstance(walked[1], FieldSelector)
    assert isinstance(walked[2], LiteralSelector)


def test_parse_trims_outer_whitespace() -> None:
    """Normalizes outer whitespace before building selector nodes."""
    selector = SelectorParser().parse(
        "  company.name  ",
        max_length=100,
        context="selector",
    )
    assert isinstance(selector, FieldSelector)
    assert selector.raw_path == "company.name"


def test_parse_rejects_empty_selector() -> None:
    """Rejects empty selectors after whitespace normalization."""
    with pytest.raises(SelectorParseError, match="cannot be empty"):
        SelectorParser().parse(
            "   ",
            max_length=100,
            context="selector",
        )


def test_parse_rejects_empty_field_path_segments() -> None:
    """Rejects malformed field selectors with empty segments."""
    with pytest.raises(ValueError, match="empty path segments"):
        SelectorParser().parse(
            "company..name",
            max_length=100,
            context="selector",
        )
