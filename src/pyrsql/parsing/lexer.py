"""Single-pass lexer for pyrsql query strings."""

from pyrsql.parsing.errors import LexError
from pyrsql.parsing.limits import ParseLimits
from pyrsql.parsing.operators import OPERATOR_SPELLINGS
from pyrsql.parsing.source import SourcePosition
from pyrsql.parsing.source import SourceSpan
from pyrsql.parsing.source import SourceText
from pyrsql.parsing.tokens import Token
from pyrsql.parsing.tokens import TokenKind

class Lexer:
    """Converts raw query text into a token stream."""

    def __init__(
        self,
        source: str | SourceText,
        *,
        limits: ParseLimits | None = None,
        operator_spellings: tuple[str, ...] = OPERATOR_SPELLINGS,
    ) -> None:
        self._source = (
            source if isinstance(source, SourceText) else SourceText(source)
        )
        self._limits = limits or ParseLimits()
        self._operator_spellings = operator_spellings
        self._index = 0
        self._line = 1
        self._column = 1
        self._validate_source_length()

    def tokenize(self) -> tuple[Token, ...]:
        """Tokenizes the configured source."""
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
            )
        )
        return tuple(tokens)

    def _next_token(self) -> Token:
        """Returns the next token from the stream."""
        if operator := self._match_operator():
            return operator

        current_char = self._peek()
        if current_char == "(":
            return self._single_char_token(TokenKind.LPAREN)
        if current_char == ")":
            return self._single_char_token(TokenKind.RPAREN)
        if current_char == ",":
            return self._single_char_token(TokenKind.COMMA)
        if current_char == ";":
            return self._single_char_token(TokenKind.SEMICOLON)
        if current_char == "'":
            return self._consume_quoted_text()
        return self._consume_unquoted_text()

    def _consume_quoted_text(self) -> Token:
        """Consumes a single-quoted text token."""
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
        """Consumes an unquoted text token."""
        start = self._current_position()
        start_index = self._index
        while not self._is_at_end():
            if self._peek().isspace():
                break
            if self._peek() in "(),;":
                break
            if self._starts_with_operator():
                break
            self._advance()

        lexeme = self._source.slice(start_index, self._index)
        if not lexeme:
            raise LexError(
                message=f"Unexpected character {self._peek()!r}",
                span=SourceSpan(start=start, end=self._current_position()),
            )

        if lexeme == "and":
            return self._make_token(TokenKind.AND, lexeme, start)
        if lexeme == "or":
            return self._make_token(TokenKind.OR, lexeme, start)

        self._enforce_selector_length(lexeme, start)
        return self._make_token(TokenKind.UNQUOTED_TEXT, lexeme, start)

    def _single_char_token(self, kind: TokenKind) -> Token:
        """Consumes a fixed-width token."""
        start = self._current_position()
        lexeme = self._advance()
        return self._make_token(kind, lexeme, start)

    def _match_operator(self) -> Token | None:
        """Consumes a comparison operator when present."""
        start = self._current_position()
        for spelling in self._operator_spellings:
            if self._source.text.startswith(spelling, self._index):
                for _ in spelling:
                    self._advance()
                return self._make_token(
                    TokenKind.COMPARISON_OPERATOR,
                    spelling,
                    start,
                )
        return None

    def _starts_with_operator(self) -> bool:
        """Checks whether the current position begins an operator."""
        for spelling in self._operator_spellings:
            if self._source.text.startswith(spelling, self._index):
                return True
        return False

    def _skip_whitespace(self) -> None:
        """Skips ASCII whitespace characters."""
        while not self._is_at_end() and self._peek().isspace():
            self._advance()

    def _validate_source_length(self) -> None:
        """Enforces the global query size limit."""
        if self._source.length > self._limits.max_query_length:
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
        """Enforces the unquoted text length limit."""
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
        """Enforces the quoted argument length limit."""
        if len(lexeme) > self._limits.max_argument_length:
            raise LexError(
                message=(
                    "Quoted token exceeds the maximum supported length of "
                    f"{self._limits.max_argument_length} characters"
                ),
                span=SourceSpan(start=position, end=self._current_position()),
            )

    def _advance(self) -> str:
        """Consumes the current character and updates source position."""
        character = self._source.text[self._index]
        self._index += 1
        if character == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return character

    def _peek(self) -> str:
        """Returns the current character without consuming it."""
        return self._source.text[self._index]

    def _current_position(self) -> SourcePosition:
        """Returns the current source position."""
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
        """Builds a token from a start position and current cursor."""
        return Token(
            kind=kind,
            lexeme=lexeme,
            span=SourceSpan(start=start, end=self._current_position()),
        )

    def _is_at_end(self) -> bool:
        """Checks whether the lexer reached the end of the source."""
        return self._index >= self._source.length
