"""Unit tests for the pyrsql lexer."""

from pyrsql.parsing.errors import LexError
from pyrsql.parsing.lexer import Lexer
from pyrsql.parsing.limits import ParseLimits
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
    try:
        Lexer("name==demo", limits=limits)
    except LexError as error:
        assert "maximum supported length" in str(error)
    else:
        raise AssertionError("Expected a LexError for an oversized query.")


def test_lexer_rejects_unterminated_strings() -> None:
    """Raises a lexical error for unterminated quoted text."""
    try:
        Lexer("name=='demo").tokenize()
    except LexError as error:
        assert "Unterminated quoted string" in str(error)
    else:
        raise AssertionError("Expected a LexError for unterminated strings.")
