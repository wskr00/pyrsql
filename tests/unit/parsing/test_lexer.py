"""Unit tests for the pyrsql lexer."""

import pytest

from pyrsql.parsing.errors import LexError
from pyrsql.parsing.lexer import Lexer
from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS, ParseLimits
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.tokens import TokenKind


def test_lexer_tokenizes_basic_expression() -> None:
    """Tokenizes a simple selector/operator/value expression."""
    tokens = Lexer("name==demo").tokenize()
    assert [token.kind for token in tokens] == [
        TokenKind.UNQUOTED_TEXT,
        TokenKind.COMPARISON_OPERATOR,
        TokenKind.UNQUOTED_TEXT,
        TokenKind.EOF,
    ]
    assert [token.lexeme for token in tokens] == ["name", "==", "demo", ""]


def test_lexer_tokenizes_logical_operators_and_parentheses() -> None:
    """Tokenizes symbolic and textual logical operators."""
    tokens = Lexer("(name==demo);city=='SP' or age=ge=18").tokenize()
    assert [token.kind for token in tokens] == [
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
    ]


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


def test_lexer_enforces_query_length_limit() -> None:
    """Rejects oversized queries before tokenization starts."""
    limits = ParseLimits(max_query_length=4)
    with pytest.raises(LexError, match="maximum supported length"):
        Lexer("name==demo", limits=limits)


def test_lexer_rejects_unterminated_strings() -> None:
    """Raises a lexical error for unterminated quoted text."""
    with pytest.raises(LexError, match="Unterminated quoted string"):
        Lexer("name=='demo").tokenize()


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


def test_lexer_skips_operator_matching_for_non_prefix_characters() -> None:
    """Avoids scanning every operator when the prefix cannot match any."""
    assert DEFAULT_OPERATOR_REGISTRY.match_candidates("n") == ()
