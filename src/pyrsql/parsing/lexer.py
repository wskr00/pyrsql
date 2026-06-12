"""Single-pass lexer for pyrsql query strings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrsql.parsing.errors import LexError
from pyrsql.parsing.normalization import (
    normalize_operator_registry,
    normalize_parse_limits,
)
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.source import SourcePosition, SourceSpan, SourceText
from pyrsql.parsing.tokens import Token, TokenKind

if TYPE_CHECKING:
    from pyrsql.parsing.limits import ParseLimits
    from pyrsql.parsing.operators import OperatorRegistry


class Lexer:
    """Converts raw query text into a token stream."""

    def __init__(
        self,
        source: str | SourceText,
        *,
        limits: ParseLimits | None = None,
        operator_registry: OperatorRegistry = DEFAULT_OPERATOR_REGISTRY,
    ) -> None:
        """Initializes the lexer with source text and parser limits."""
        self._text = self._normalize_source(source).text
        self._length = len(self._text)
        self._limits = normalize_parse_limits(limits, owner_type=type(self))
        self._operator_registry = normalize_operator_registry(
            operator_registry,
            owner_type=type(self),
        )
        self._index = 0
        self._line = 1
        self._column = 1
        self._validate_source_length()

    @staticmethod
    def _normalize_source(source: str | SourceText) -> SourceText:
        """Normalizes the lexer source input.

        Returns:
            A wrapped immutable source object.

        Raises:
            TypeError: If the source is neither raw text nor ``SourceText``.
        """
        if isinstance(source, SourceText):
            return source
        if not isinstance(source, str):
            raise TypeError("Lexer source must be a string or SourceText.")
        return SourceText(text=source)

    @property
    def limits(self) -> ParseLimits:
        """Returns the configured parser safety limits.

        Returns:
            The lexer safety limits currently in use.
        """
        return self._limits

    def tokenize(self) -> tuple[Token, ...]:
        """Tokenizes the configured source.

        Returns:
            The tokenized source stream.
        """
        tokens: list[Token] = []
        while not self._is_at_end():
            self._skip_whitespace()
            if self._is_at_end():
                break
            tokens.append(self._next_token())
        tokens.append(
            self._make_token(
                TokenKind.EOF,
                "",
                self._current_position(),
            ),
        )
        return tuple(tokens)

    def _next_token(self) -> Token:
        """Returns the next token from the stream.

        Returns:
            The next token in source order.
        """
        if operator := self._match_operator():
            return operator

        current_char = self._peek()
        match current_char:
            case "(":
                return self._single_char_token(TokenKind.LPAREN)
            case ")":
                return self._single_char_token(TokenKind.RPAREN)
            case ",":
                return self._single_char_token(TokenKind.COMMA)
            case ";":
                return self._single_char_token(TokenKind.SEMICOLON)
            case "'":
                return self._consume_quoted_text()
            case _:
                return self._consume_unquoted_text()

    def _consume_quoted_text(self) -> Token:
        """Consumes a single-quoted text token.

        Returns:
            The consumed quoted token.

        Raises:
            LexError: If the quoted text is unterminated.
        """
        start = self._current_position()
        self._advance()
        characters: list[str] = []
        while not self._is_at_end():
            current_char = self._advance()
            if current_char == "'":
                lexeme = "".join(characters)
                self._enforce_argument_length(lexeme, start)
                return self._make_token(TokenKind.QUOTED_TEXT, lexeme, start)
            if current_char == "\\" and not self._is_at_end():
                escaped_char = self._advance()
                characters.append(escaped_char)
                continue
            characters.append(current_char)
        raise LexError(
            message="Unterminated quoted string",
            span=SourceSpan(start=start, end=self._current_position()),
        )

    def _consume_unquoted_text(self) -> Token:
        """Consumes an unquoted text token.

        Returns:
            The consumed unquoted token.

        Raises:
            LexError: If the current character cannot start a token.
        """
        start = self._current_position()
        start_index = self._index
        while not self._is_at_end():
            current_char = self._peek()
            if current_char.isspace():
                break
            if current_char in "(),;":
                break
            if self._match_operator_spelling(current_char) is not None:
                break
            self._advance()

        lexeme = self._text[start_index : self._index]
        if not lexeme:
            raise LexError(
                message=f"Unexpected character {self._peek()!r}",
                span=SourceSpan(start=start, end=self._current_position()),
            )

        match lexeme:
            case "and":
                return self._make_token(TokenKind.AND, lexeme, start)
            case "or":
                return self._make_token(TokenKind.OR, lexeme, start)
            case _:
                pass

        self._enforce_selector_length(lexeme, start)
        return self._make_token(TokenKind.UNQUOTED_TEXT, lexeme, start)

    def _single_char_token(self, kind: TokenKind) -> Token:
        """Consumes a fixed-width token.

        Returns:
            The consumed single-character token.
        """
        start = self._current_position()
        lexeme = self._advance()
        return self._make_token(kind, lexeme, start)

    def _match_operator(self) -> Token | None:
        """Consumes a comparison operator when present.

        Returns:
            The matched operator token, or ``None``.
        """
        spelling = self._match_operator_spelling()
        if spelling is None:
            return None
        start = self._current_position()
        self._advance_operator(spelling)
        return self._make_token(
            TokenKind.COMPARISON_OPERATOR,
            spelling,
            start,
        )

    def _match_operator_spelling(
        self,
        prefix: str | None = None,
    ) -> str | None:
        """Returns the matching operator spelling at the current cursor.

        Returns:
            The matched operator spelling, or ``None``.
        """
        current_prefix = prefix or self._peek()
        for spelling in self._operator_registry.match_candidates(
            current_prefix,
        ):
            if self._text.startswith(spelling, self._index):
                return spelling
        return None

    def _skip_whitespace(self) -> None:
        """Skips ASCII whitespace characters."""
        while not self._is_at_end():
            if not self._peek().isspace():
                break
            self._advance()

    def _validate_source_length(self) -> None:
        """Enforces the global query size limit.

        Raises:
            LexError: If the source exceeds the configured length.
        """
        if self._length > self._limits.max_query_length:
            position = SourcePosition(index=0, line=1, column=1)
            raise LexError(
                message=(
                    "Query exceeds the maximum supported length of "
                    f"{self._limits.max_query_length} characters"
                ),
                span=SourceSpan(start=position, end=position),
            )

    def _enforce_selector_length(
        self,
        lexeme: str,
        position: SourcePosition,
    ) -> None:
        """Enforces the unquoted text length limit.

        Raises:
            LexError: If the unquoted token exceeds the configured length.
        """
        if len(lexeme) > self._limits.max_selector_length:
            raise LexError(
                message=(
                    "Unquoted token exceeds the maximum supported length of "
                    f"{self._limits.max_selector_length} characters"
                ),
                span=SourceSpan(start=position, end=self._current_position()),
            )

    def _enforce_argument_length(
        self,
        lexeme: str,
        position: SourcePosition,
    ) -> None:
        """Enforces the quoted argument length limit.

        Raises:
            LexError: If the quoted token exceeds the configured length.
        """
        if len(lexeme) > self._limits.max_argument_length:
            raise LexError(
                message=(
                    "Quoted token exceeds the maximum supported length of "
                    f"{self._limits.max_argument_length} characters"
                ),
                span=SourceSpan(start=position, end=self._current_position()),
            )

    def _advance(self) -> str:
        """Consumes the current character and updates source position.

        Returns:
            The consumed character.
        """
        character = self._text[self._index]
        self._index += 1
        if character == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return character

    def _advance_operator(self, operator: str) -> None:
        """Consumes a comparison operator in one step."""
        self._index += len(operator)
        self._column += len(operator)

    def _peek(self) -> str:
        """Returns the current character without consuming it.

        Returns:
            The current character.
        """
        return self._text[self._index]

    def _current_position(self) -> SourcePosition:
        """Returns the current source position.

        Returns:
            The current source position.
        """
        return SourcePosition(
            index=self._index,
            line=self._line,
            column=self._column,
        )

    def _make_token(
        self,
        kind: TokenKind,
        lexeme: str,
        start: SourcePosition,
    ) -> Token:
        """Builds a token from a start position and current cursor.

        Returns:
            The constructed token.
        """
        return Token(
            kind=kind,
            lexeme=lexeme,
            span=SourceSpan(start=start, end=self._current_position()),
        )

    def _is_at_end(self) -> bool:
        """Checks whether the lexer reached the end of the source.

        Returns:
            ``True`` when the lexer cursor reached the end of input.
        """
        return self._index >= self._length
