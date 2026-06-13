"""Unit tests for the pyrsql lexer."""

from __future__ import annotations

import pytest

from pyrsql.parsing.errors import LexError
from pyrsql.parsing.lexer import Lexer
from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS, ParseLimits
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.tokens import TokenKind


@pytest.mark.parametrize(
    ("source", "expected_kinds", "expected_lexemes"),
    [
        pytest.param(
            "name==demo",
            (
                TokenKind.UNQUOTED_TEXT,
                TokenKind.COMPARISON_OPERATOR,
                TokenKind.UNQUOTED_TEXT,
                TokenKind.EOF,
            ),
            ("name", "==", "demo", ""),
            id="basic-expression",
        ),
        pytest.param(
            "(name==demo);city=='SP' or age=ge=18",
            (
                TokenKind.LPAREN,
                TokenKind.UNQUOTED_TEXT,
                TokenKind.COMPARISON_OPERATOR,
                TokenKind.UNQUOTED_TEXT,
                TokenKind.RPAREN,
                TokenKind.SEMICOLON,
                TokenKind.UNQUOTED_TEXT,
                TokenKind.COMPARISON_OPERATOR,
                TokenKind.QUOTED_TEXT,
                TokenKind.OR,
                TokenKind.UNQUOTED_TEXT,
                TokenKind.COMPARISON_OPERATOR,
                TokenKind.UNQUOTED_TEXT,
                TokenKind.EOF,
            ),
            None,
            id="logical-operators-and-parentheses",
        ),
    ],
)
def test_lexer_tokenizes_supported_expressions(
    source: str,
    expected_kinds: tuple[TokenKind, ...],
    expected_lexemes: tuple[str, ...] | None,
) -> None:
    """Tokenizes basic expressions, grouping, and logical operators."""
    tokens = Lexer(source).tokenize()

    assert tuple(token.kind for token in tokens) == expected_kinds
    if expected_lexemes is not None:
        assert tuple(token.lexeme for token in tokens) == expected_lexemes


def test_lexer_prefers_the_longest_matching_operator() -> None:
    """Uses the longest available operator alias at a position."""
    tokens = Lexer("age>=18").tokenize()

    assert tokens[1].kind is TokenKind.COMPARISON_OPERATOR
    assert tokens[1].lexeme == ">="


def test_lexer_unescapes_quoted_text() -> None:
    """Consumes quoted strings and preserves escaped characters."""
    tokens = Lexer(r"name=='de\'mo'").tokenize()

    assert tokens[2].kind is TokenKind.QUOTED_TEXT
    assert tokens[2].lexeme == "de'mo"


def test_lexer_tracks_source_positions() -> None:
    """Records token spans with line and column information."""
    tokens = Lexer("name==demo").tokenize()

    assert tokens[0].span.start.line == 1
    assert tokens[0].span.start.column == 1
    assert tokens[0].span.end.column == 5
    assert tokens[1].span.start.column == 5
    assert tokens[2].span.start.column == 7


@pytest.mark.parametrize(
    ("source", "limits", "pattern"),
    [
        pytest.param(
            "name==demo",
            ParseLimits(max_query_length=4),
            r"maximum supported length",
            id="query-length-limit",
        ),
        pytest.param(
            "name=='demo",
            None,
            r"Unterminated quoted string",
            id="unterminated-string",
        ),
    ],
)
def test_lexer_raises_structured_errors_for_invalid_input(
    source: str,
    limits: ParseLimits | None,
    pattern: str,
) -> None:
    """Raises lexical errors with the expected user-facing message."""
    with pytest.raises(LexError, match=pattern):
        Lexer(source, limits=limits).tokenize()


def test_lexer_error_exposes_structured_diagnostic() -> None:
    """Exposes a structured diagnostic on lexical failures."""
    with pytest.raises(LexError) as exc_info:
        Lexer("name=='demo").tokenize()

    assert exc_info.value.code == "lex_error"
    assert exc_info.value.diagnostic.code == "lex_error"


def test_lexer_uses_shared_default_limits_instance() -> None:
    """Reuses the shared default limits on the common path."""
    lexer = Lexer("name==demo")

    assert lexer.limits is DEFAULT_PARSE_LIMITS


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {"source": 123},
            r"string or SourceText",
            id="invalid-source",
        ),
        pytest.param(
            {"source": "name==demo", "limits": object()},
            r"ParseLimits instance",
            id="invalid-limits",
        ),
        pytest.param(
            {
                "source": "name==demo",
                "operator_registry": object(),
            },
            r"OperatorRegistry instance",
            id="invalid-operator-registry",
        ),
    ],
)
def test_lexer_rejects_invalid_runtime_dependencies(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """Lexer validates public constructor dependencies eagerly."""
    with pytest.raises(TypeError, match=pattern):
        Lexer(**kwargs)  # type: ignore[arg-type]


def test_lexer_skips_operator_matching_for_non_prefix_characters() -> None:
    """Avoids scanning every operator when the prefix cannot match any."""
    assert DEFAULT_OPERATOR_REGISTRY.match_candidates("n") == ()
