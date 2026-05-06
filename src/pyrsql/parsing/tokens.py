"""Token models for the lexer."""

from enum import Enum, auto

import msgspec

from pyrsql.parsing.source import SourceSpan


class TokenKind(Enum):
    """Token kinds emitted by the lexer."""

    EOF = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    SEMICOLON = auto()
    AND = auto()
    OR = auto()
    COMPARISON_OPERATOR = auto()
    UNQUOTED_TEXT = auto()
    QUOTED_TEXT = auto()


class Token(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a lexical token."""

    kind: TokenKind
    lexeme: str
    span: SourceSpan
