"""Unit tests for the shared selector parser."""

from __future__ import annotations

import pytest

from pyrsql.selector.ast import FieldSelector, FunctionSelector, LiteralSelector
from pyrsql.selector.parser import SelectorParseError, SelectorParser


@pytest.mark.parametrize(
    ("text", "delimiter", "expected"),
    [
        pytest.param(
            "  name  | @upper[ city ] |   | #123  ",
            "|",
            ("name", "@upper[ city ]", "#123"),
            id="trim-and-drop-blank-fragments",
        ),
    ],
)
def test_split_top_level_normalizes_fragments(
    text: str,
    delimiter: str,
    expected: tuple[str, ...],
) -> None:
    """Splits top-level fragments into normalized non-empty parts."""
    parser = SelectorParser()

    assert parser.split_top_level(text, delimiter=delimiter) == expected


@pytest.mark.parametrize(
    ("text", "delimiter", "expected_error", "pattern"),
    [
        pytest.param(
            None,
            "|",
            TypeError,
            r"text must be a string",
            id="non-string-text",
        ),
        pytest.param(
            "a|b",
            "",
            ValueError,
            r"single character",
            id="empty-delimiter",
        ),
        pytest.param(
            "a||b",
            "||",
            ValueError,
            r"single character",
            id="multi-character-delimiter",
        ),
    ],
)
def test_split_top_level_rejects_invalid_runtime_inputs(
    text: object,
    delimiter: object,
    expected_error: type[Exception],
    pattern: str,
) -> None:
    """Top-level splitting enforces a strict runtime contract."""
    with pytest.raises(expected_error, match=pattern):
        SelectorParser().split_top_level(text, delimiter=delimiter)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw_selector", "expected_type", "expected_value"),
    [
        pytest.param(
            "company.name",
            FieldSelector,
            "company.name",
            id="field-selector",
        ),
        pytest.param(
            "  company.name  ",
            FieldSelector,
            "company.name",
            id="trimmed-field-selector",
        ),
        pytest.param(
            "#true",
            LiteralSelector,
            True,
            id="literal-selector",
        ),
    ],
)
def test_parse_supports_field_and_literal_selectors(
    raw_selector: str,
    expected_type: type[FieldSelector | LiteralSelector],
    expected_value: object,
) -> None:
    """Parses field and literal selectors into the expected node types."""
    selector = SelectorParser().parse(
        raw_selector,
        max_length=100,
        context="selector",
    )

    assert isinstance(selector, expected_type)
    if isinstance(selector, FieldSelector):
        assert selector.raw_path == expected_value
    else:
        assert selector.value is expected_value


def test_parse_function_selector_walks_nested_arguments() -> None:
    """Parses nested function selectors into a traversable syntax tree."""
    selector = SelectorParser().parse(
        "@upper[name|#1]",
        max_length=100,
        context="selector",
    )
    walked = tuple(selector.walk())

    assert isinstance(selector, FunctionSelector)
    assert isinstance(walked[1], FieldSelector)
    assert isinstance(walked[2], LiteralSelector)


@pytest.mark.parametrize(
    ("raw_selector", "pattern", "expected_error"),
    [
        pytest.param(
            "   ",
            r"cannot be empty",
            SelectorParseError,
            id="empty-selector",
        ),
        pytest.param(
            "company..name",
            r"empty path segments",
            ValueError,
            id="empty-field-segment",
        ),
        pytest.param(
            "@upper[name",
            r"invalid function selector|unbalanced brackets",
            SelectorParseError,
            id="invalid-function-selector",
        ),
        pytest.param(
            "@upper[name||#1]",
            r"cannot contain empty arguments",
            SelectorParseError,
            id="empty-function-argument-middle",
        ),
        pytest.param(
            "@upper[|name]",
            r"cannot contain empty arguments",
            SelectorParseError,
            id="empty-function-argument-leading",
        ),
        pytest.param(
            "@upper[name|]",
            r"cannot contain empty arguments",
            SelectorParseError,
            id="empty-function-argument-trailing",
        ),
    ],
)
def test_parse_rejects_invalid_selectors(
    raw_selector: str,
    pattern: str,
    expected_error: type[Exception],
) -> None:
    """Rejects invalid selector shapes through structured errors."""
    with pytest.raises(expected_error, match=pattern):
        SelectorParser().parse(
            raw_selector,
            max_length=100,
            context="selector",
        )


@pytest.mark.parametrize(
    ("kwargs", "expected_error", "pattern"),
    [
        pytest.param(
            {"raw_selector": "name", "max_length": 1.5, "context": "selector"},
            TypeError,
            r"max_length must be an integer",
            id="non-integer-max-length",
        ),
        pytest.param(
            {"raw_selector": "name", "max_length": True, "context": "selector"},
            TypeError,
            r"max_length must be an integer",
            id="bool-max-length",
        ),
        pytest.param(
            {"raw_selector": "name", "max_length": 0, "context": "selector"},
            ValueError,
            r"greater than 0",
            id="non-positive-max-length",
        ),
        pytest.param(
            {"raw_selector": "name", "max_length": 10, "context": None},
            TypeError,
            r"context must be a string",
            id="non-string-context",
        ),
        pytest.param(
            {"raw_selector": "name", "max_length": 10, "context": ""},
            ValueError,
            r"context cannot be empty",
            id="empty-context",
        ),
    ],
)
def test_parse_rejects_invalid_runtime_inputs(
    kwargs: dict[str, object],
    expected_error: type[Exception],
    pattern: str,
) -> None:
    """Selector parsing rejects invalid runtime inputs early."""
    with pytest.raises(expected_error, match=pattern):
        SelectorParser().parse(**kwargs)  # type: ignore[arg-type]
