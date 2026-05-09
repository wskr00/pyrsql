"""Recursive-descent parser for pyrsql token streams."""

from pyrsql.parsing.ast import (
    Argument,
    ComparisonNode,
    Expression,
    LogicalNode,
    LogicalOperator,
)
from pyrsql.parsing.errors import ParseError
from pyrsql.parsing.lexer import Lexer
from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS, ParseLimits
from pyrsql.parsing.operators import (
    DEFAULT_OPERATOR_REGISTRY,
    ComparisonOperator,
    OperatorRegistry,
)
from pyrsql.parsing.source import SourceSpan
from pyrsql.parsing.tokens import Token, TokenKind
from pyrsql.selector.ast import SelectorNode
from pyrsql.selector.parser import DEFAULT_SELECTOR_PARSER, SelectorParseError

_EXPRESSION_TERMINATORS = (
    TokenKind.EOF,
    TokenKind.RPAREN,
    TokenKind.AND,
    TokenKind.OR,
    TokenKind.SEMICOLON,
    TokenKind.COMMA,
)


class Parser:
    """Parses pyrsql query strings into AST nodes.

    The parser consumes a token stream and builds a syntax tree that later
    semantic analysis and ORM compilation stages can consume.
    """

    def __init__(
        self,
        source: str,
        *,
        limits: ParseLimits | None = None,
        operator_registry: OperatorRegistry = DEFAULT_OPERATOR_REGISTRY,
    ) -> None:
        """Initializes the parser with raw source text and limits."""
        self._limits = limits or DEFAULT_PARSE_LIMITS
        self._operator_registry = operator_registry
        self._tokens = Lexer(
            source,
            limits=self._limits,
            operator_registry=operator_registry,
        ).tokenize()
        self._selector_parser = DEFAULT_SELECTOR_PARSER
        self._index = 0
        self._node_count = 0

    @property
    def limits(self) -> ParseLimits:
        """Returns the configured parser safety limits.

        Returns:
            The parser safety limits currently in use.
        """
        return self._limits

    def parse(self) -> Expression:
        """Parses the configured query into an AST.

        Returns:
            The parsed expression tree.
        """
        node = self._parse_or_expression(depth=1)
        self._expect(TokenKind.EOF, message="Unexpected trailing tokens")
        return node

    def _parse_or_expression(self, depth: int) -> Expression:
        """Parses OR-precedence logical expressions.

        Returns:
            The parsed expression subtree.
        """
        self._enforce_depth(depth)
        nodes = [self._parse_and_expression(depth + 1)]
        while self._match(TokenKind.OR, TokenKind.COMMA):
            nodes.append(self._parse_and_expression(depth + 1))
        if len(nodes) == 1:
            return nodes[0]
        return self._make_logical_node(LogicalOperator.OR, nodes)

    def _parse_and_expression(self, depth: int) -> Expression:
        """Parses AND-precedence logical expressions.

        Returns:
            The parsed expression subtree.
        """
        self._enforce_depth(depth)
        nodes = [self._parse_primary_expression(depth + 1)]
        while self._match(TokenKind.AND, TokenKind.SEMICOLON):
            nodes.append(self._parse_primary_expression(depth + 1))
        if len(nodes) == 1:
            return nodes[0]
        return self._make_logical_node(LogicalOperator.AND, nodes)

    def _parse_primary_expression(self, depth: int) -> Expression:
        """Parses grouped or comparison expressions.

        Returns:
            The parsed primary expression.
        """
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
        """Parses a comparison expression.

        Returns:
            The parsed comparison node.

        Raises:
            ParseError: If the comparison syntax is invalid.
        """
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
        """Parses comparison arguments.

        Returns:
            The parsed comparison arguments.
        """
        if self._current().kind is TokenKind.LPAREN:
            return self._parse_argument_list()
        if self._current().kind in _EXPRESSION_TERMINATORS:
            return ()
        argument_token = self._expect_value("Expected a comparison argument")
        return (self._make_argument(argument_token),)

    def _parse_argument_list(self) -> tuple[Argument, ...]:
        """Parses a parenthesized argument list.

        Returns:
            The parsed argument list.

        Raises:
            ParseError: If the argument list is malformed or exceeds limits.
        """
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
                "Expected an argument inside list",
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
        """Validates operator arity.

        Raises:
            ParseError: If the number of arguments does not match the
                operator's arity.
        """
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
        """Builds a logical node while tracking parser limits.

        Returns:
            The constructed logical node.
        """
        self._register_node()
        return LogicalNode(
            span=SourceSpan.cover(children[0].span, children[-1].span),
            operator=operator,
            children=tuple(children),
        )

    def _make_comparison_node(
        self,
        selector_token: Token,
        selector: SelectorNode,
        operator_token: Token,
        operator: ComparisonOperator,
        arguments: tuple[Argument, ...],
    ) -> ComparisonNode:
        """Builds a comparison node while tracking parser limits.

        Returns:
            The constructed comparison node.
        """
        self._register_node()
        end_span = arguments[-1].span if arguments else operator_token.span
        return ComparisonNode(
            span=SourceSpan.cover(selector_token.span, end_span),
            selector=selector,
            operator=operator,
            arguments=arguments,
        )

    def _make_argument(self, token: Token) -> Argument:
        """Builds an argument node from a value token.

        Returns:
            The constructed argument node.
        """
        return Argument(
            text=token.lexeme,
            quoted=token.kind is TokenKind.QUOTED_TEXT,
            span=token.span,
        )

    def _expect_value(self, message: str) -> Token:
        """Consumes the next value token.

        Returns:
            The consumed value token.

        Raises:
            ParseError: If the current token is not a value token.
        """
        current = self._current()
        if current.kind not in (TokenKind.UNQUOTED_TEXT, TokenKind.QUOTED_TEXT):
            raise ParseError(message=message, span=current.span)
        self._advance()
        return current

    def _expect(self, kind: TokenKind, *, message: str) -> Token:
        """Consumes the next token if it matches the expected kind.

        Returns:
            The consumed token.

        Raises:
            ParseError: If the current token kind does not match.
        """
        current = self._current()
        if current.kind is not kind:
            raise ParseError(message=message, span=current.span)
        self._advance()
        return current

    def _match(self, *kinds: TokenKind) -> bool:
        """Consumes the current token if it matches one of the kinds.

        Returns:
            ``True`` when a token was consumed.
        """
        if self._current().kind in kinds:
            self._advance()
            return True
        return False

    def _register_node(self) -> None:
        """Tracks AST node creation against parser limits.

        Raises:
            ParseError: If the node count exceeds the configured limit.
        """
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
        """Enforces the maximum expression depth.

        Raises:
            ParseError: If the expression depth exceeds the configured limit.
        """
        if depth > self._limits.max_expression_depth:
            raise ParseError(
                message=(
                    "Query exceeds the maximum supported expression depth of "
                    f"{self._limits.max_expression_depth}"
                ),
                span=self._current().span,
            )

    def _current(self) -> Token:
        """The current token.

        Returns:
            The current token.
        """
        return self._tokens[self._index]

    def _advance(self) -> None:
        """Advances to the next token when possible."""
        if self._index < len(self._tokens) - 1:
            self._index += 1
