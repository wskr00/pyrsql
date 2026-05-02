"""Recursive-descent parser for pyrsql token streams."""

from pyrsql.parsing.ast import Argument
from pyrsql.parsing.ast import ComparisonNode
from pyrsql.parsing.ast import Expression
from pyrsql.parsing.ast import LogicalNode
from pyrsql.parsing.ast import LogicalOperator
from pyrsql.parsing.errors import ParseError
from pyrsql.parsing.lexer import Lexer
from pyrsql.parsing.limits import ParseLimits
from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.operators import OperatorRegistry
from pyrsql.parsing.source import SourceSpan
from pyrsql.parsing.tokens import Token
from pyrsql.parsing.tokens import TokenKind
from pyrsql.selector.ast import Selector
from pyrsql.selector.parser import SelectorParseError
from pyrsql.selector.parser import SelectorParser


class Parser:
    """Builds an AST from a pyrsql query string."""

    def __init__(
        self,
        source: str,
        *,
        limits: ParseLimits | None = None,
        operator_registry: OperatorRegistry = DEFAULT_OPERATOR_REGISTRY,
    ) -> None:
        self._limits = limits or ParseLimits()
        self._operator_registry = operator_registry
        self._tokens = Lexer(
            source,
            limits=self._limits,
            operator_spellings=operator_registry.operator_spellings,
        ).tokenize()
        self._selector_parser = SelectorParser()
        self._index = 0
        self._node_count = 0

    def parse(self) -> Expression:
        """Parses the configured query into an AST."""
        node = self._parse_or_expression(depth=1)
        self._expect(TokenKind.EOF, message="Unexpected trailing tokens")
        return node

    def _parse_or_expression(self, depth: int) -> Expression:
        """Parses OR-precedence logical expressions."""
        self._enforce_depth(depth)
        nodes = [self._parse_and_expression(depth + 1)]
        while self._match(TokenKind.OR, TokenKind.COMMA):
            nodes.append(self._parse_and_expression(depth + 1))
        if len(nodes) == 1:
            return nodes[0]
        return self._make_logical_node(LogicalOperator.OR, nodes)

    def _parse_and_expression(self, depth: int) -> Expression:
        """Parses AND-precedence logical expressions."""
        self._enforce_depth(depth)
        nodes = [self._parse_primary_expression(depth + 1)]
        while self._match(TokenKind.AND, TokenKind.SEMICOLON):
            nodes.append(self._parse_primary_expression(depth + 1))
        if len(nodes) == 1:
            return nodes[0]
        return self._make_logical_node(LogicalOperator.AND, nodes)

    def _parse_primary_expression(self, depth: int) -> Expression:
        """Parses grouped or comparison expressions."""
        self._enforce_depth(depth)
        if self._current().kind is TokenKind.LPAREN:
            opening = self._expect(
                TokenKind.LPAREN,
                message="Expected '(' to start grouped expression",
            )
            expression = self._parse_or_expression(depth + 1)
            closing = self._expect(
                TokenKind.RPAREN,
                message="Expected ')' to close grouped expression",
            )
            return expression.with_span(
                SourceSpan.cover(opening.span, closing.span),
            )
        return self._parse_comparison()

    def _parse_comparison(self) -> ComparisonNode:
        """Parses a comparison expression."""
        selector = self._expect(
            TokenKind.UNQUOTED_TEXT,
            message="Expected a selector before the comparison operator",
        )
        try:
            parsed_selector = self._selector_parser.parse(
                selector.lexeme,
                max_length=self._limits.max_selector_length,
                context="Comparison selector",
            )
        except SelectorParseError as error:
            raise ParseError(message=str(error), span=selector.span) from error
        operator_token = self._expect(
            TokenKind.COMPARISON_OPERATOR,
            message="Expected a comparison operator after the selector",
        )
        operator = self._operator_registry.get(operator_token.lexeme)
        arguments = self._parse_arguments()
        self._validate_argument_count(operator_token, operator, arguments)
        return self._make_comparison_node(
            selector,
            parsed_selector,
            operator_token,
            operator,
            arguments,
        )

    def _parse_arguments(self) -> tuple[Argument, ...]:
        """Parses comparison arguments."""
        if self._current().kind is TokenKind.LPAREN:
            return self._parse_argument_list()
        if self._current().kind in (
            TokenKind.EOF,
            TokenKind.RPAREN,
            TokenKind.AND,
            TokenKind.OR,
            TokenKind.SEMICOLON,
            TokenKind.COMMA,
        ):
            return ()
        argument_token = self._expect_value("Expected a comparison argument")
        return (self._make_argument(argument_token),)

    def _parse_argument_list(self) -> tuple[Argument, ...]:
        """Parses a parenthesized argument list."""
        self._expect(
            TokenKind.LPAREN,
            message="Expected '(' to start argument list",
        )
        arguments: list[Argument] = []
        if self._current().kind is TokenKind.RPAREN:
            self._advance()
            return ()

        while True:
            if len(arguments) >= self._limits.max_arguments_per_list:
                raise ParseError(
                    message=(
                        "Argument list exceeds the maximum supported size of "
                        f"{self._limits.max_arguments_per_list}"
                    ),
                    span=self._current().span,
                )
            argument_token = self._expect_value(
                "Expected an argument inside list"
            )
            arguments.append(self._make_argument(argument_token))
            if self._match(TokenKind.COMMA):
                continue
            self._expect(
                TokenKind.RPAREN,
                message="Expected ')' to close argument list",
            )
            return tuple(arguments)

    def _validate_argument_count(
        self,
        operator_token: Token,
        operator: ComparisonOperator,
        arguments: tuple[Argument, ...],
    ) -> None:
        """Validates operator arity."""
        minimum_arguments = operator.minimum_arguments
        maximum_arguments = operator.maximum_arguments
        if len(arguments) < minimum_arguments:
            raise ParseError(
                message=(
                    f"Operator {operator_token.lexeme!r} expects at least "
                    f"{minimum_arguments} argument(s)"
                ),
                span=operator_token.span,
            )
        if maximum_arguments is not None and len(arguments) > maximum_arguments:
            raise ParseError(
                message=(
                    f"Operator {operator_token.lexeme!r} expects at most "
                    f"{maximum_arguments} argument(s)"
                ),
                span=operator_token.span,
            )

    def _make_logical_node(
        self,
        operator: LogicalOperator,
        children: list[Expression],
    ) -> LogicalNode:
        """Builds a logical node while tracking parser limits."""
        self._register_node()
        return LogicalNode(
            span=SourceSpan.cover(children[0].span, children[-1].span),
            operator=operator,
            children=tuple(children),
        )

    def _make_comparison_node(
        self,
        selector_token: Token,
        selector: Selector,
        operator_token: Token,
        operator: ComparisonOperator,
        arguments: tuple[Argument, ...],
    ) -> ComparisonNode:
        """Builds a comparison node while tracking parser limits."""
        self._register_node()
        end_span = arguments[-1].span if arguments else operator_token.span
        return ComparisonNode(
            span=SourceSpan.cover(selector_token.span, end_span),
            selector=selector,
            operator=operator,
            arguments=arguments,
        )

    def _make_argument(self, token: Token) -> Argument:
        """Builds an argument node from a value token."""
        return Argument(
            text=token.lexeme,
            quoted=token.kind is TokenKind.QUOTED_TEXT,
            span=token.span,
        )

    def _expect_value(self, message: str) -> Token:
        """Consumes the next value token."""
        current = self._current()
        if current.kind not in (TokenKind.UNQUOTED_TEXT, TokenKind.QUOTED_TEXT):
            raise ParseError(message=message, span=current.span)
        self._advance()
        return current

    def _expect(self, kind: TokenKind, *, message: str) -> Token:
        """Consumes the next token if it matches the expected kind."""
        current = self._current()
        if current.kind is not kind:
            raise ParseError(message=message, span=current.span)
        self._advance()
        return current

    def _match(self, *kinds: TokenKind) -> bool:
        """Consumes the current token if it matches one of the kinds."""
        if self._current().kind in kinds:
            self._advance()
            return True
        return False

    def _register_node(self) -> None:
        """Tracks AST node creation against parser limits."""
        self._node_count += 1
        if self._node_count > self._limits.max_node_count:
            raise ParseError(
                message=(
                    "Query exceeds the maximum supported node count of "
                    f"{self._limits.max_node_count}"
                ),
                span=self._current().span,
            )

    def _enforce_depth(self, depth: int) -> None:
        """Enforces the maximum expression depth."""
        if depth > self._limits.max_expression_depth:
            raise ParseError(
                message=(
                    "Query exceeds the maximum supported expression depth of "
                    f"{self._limits.max_expression_depth}"
                ),
                span=self._current().span,
            )

    def _current(self) -> Token:
        """Returns the current token."""
        return self._tokens[self._index]

    def _advance(self) -> None:
        """Advances to the next token when possible."""
        if self._index < len(self._tokens) - 1:
            self._index += 1
