"""Token models for the lexer."""

from dataclasses import dataclass
from enum import Enum, auto

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


@dataclass(frozen=True, slots=True)
class Token:
    """Represents a lexical token."""

    kind: TokenKind
    lexeme: str
    span: SourceSpan
