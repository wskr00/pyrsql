"""Unit tests for the pyrsql parser."""

import pytest

from pyrsql.parsing.ast import ComparisonNode, LogicalNode, LogicalOperator
from pyrsql.parsing.errors import ParseError
from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS, ParseLimits
from pyrsql.parsing.operators import (
    DEFAULT_OPERATOR_REGISTRY,
    ComparisonOperator,
    OperatorRegistry,
)
from pyrsql.parsing.parser import Parser
from pyrsql.selector.ast import (
    FieldSelector,
    FunctionSelector,
    LiteralSelector,
)


def test_parser_builds_comparison_node() -> None:
    """Parses a simple comparison."""
    expression = Parser("name==demo").parse()
    assert isinstance(expression, ComparisonNode)
    assert isinstance(expression.selector, FieldSelector)
    assert expression.selector.raw_path == "name"
    assert expression.operator.name == "equal"
    assert tuple(argument.text for argument in expression.arguments) == (
        "demo",
    )


def test_parser_preserves_and_or_precedence() -> None:
    """Parses AND more tightly than OR."""
    expression = Parser("name==demo,city==sp;age=ge=18").parse()
    assert isinstance(expression, LogicalNode)
    assert expression.operator is LogicalOperator.OR
    assert isinstance(expression.children[0], ComparisonNode)
    assert isinstance(expression.children[1], LogicalNode)
    assert expression.children[1].operator is LogicalOperator.AND


def test_parser_parses_argument_list() -> None:
    """Parses IN lists as multiple arguments."""
    expression = Parser("id=in=(1,2,3)").parse()
    assert isinstance(expression, ComparisonNode)
    assert tuple(argument.text for argument in expression.arguments) == (
        "1",
        "2",
        "3",
    )


def test_parser_expands_grouped_expression_span() -> None:
    """Expands grouped expressions to cover the surrounding parentheses."""
    expression = Parser("(name==demo)").parse()
    assert expression.span.start.column == 1
    assert expression.span.end.column == len("(name==demo)") + 1


def test_parser_parses_function_selector_in_comparison() -> None:
    """Parses nested function selectors in comparison expressions."""
    expression = Parser("@concat[@upper[name]|#123]==demo").parse()
    assert isinstance(expression, ComparisonNode)
    assert isinstance(expression.selector, FunctionSelector)
    assert expression.selector.function_name == "concat"
    assert isinstance(expression.selector.arguments[0], FunctionSelector)
    assert isinstance(expression.selector.arguments[1], LiteralSelector)


def test_parser_ast_walk_traverses_logical_tree() -> None:
    """Traverses the syntax tree depth-first."""
    expression = Parser("name==demo;city==sp").parse()
    walked = tuple(expression.walk())
    assert isinstance(walked[0], LogicalNode)
    assert isinstance(walked[1], ComparisonNode)
    assert isinstance(walked[2], ComparisonNode)


def test_parser_allows_nullary_null_check() -> None:
    """Allows null-check operators without explicit arguments."""
    expression = Parser("company.code=na=").parse()
    assert isinstance(expression, ComparisonNode)
    assert expression.operator.name == "is_null"
    assert not expression.arguments


def test_parser_accepts_custom_operator_registry() -> None:
    """Parses custom operators registered through the parser."""
    all_match = ComparisonOperator(
        name="all_match",
        spellings=("=all=",),
        minimum_arguments=1,
        maximum_arguments=1,
    )
    registry = OperatorRegistry(
        operators=DEFAULT_OPERATOR_REGISTRY.operators + (all_match,)
    )
    expression = Parser(
        "name=all=demo",
        operator_registry=registry,
    ).parse()
    assert isinstance(expression, ComparisonNode)
    assert expression.operator.name == "all_match"


def test_parser_rejects_missing_required_argument() -> None:
    """Rejects operators that require arguments when none are given."""
    with pytest.raises(ParseError, match="expects at least"):
        Parser("name==").parse()


def test_parser_enforces_depth_limit() -> None:
    """Rejects overly deep expressions."""
    limits = ParseLimits(max_expression_depth=2)
    with pytest.raises(ParseError, match="maximum supported expression depth"):
        Parser("((name==demo))", limits=limits).parse()


def test_parse_limits_reject_invalid_values() -> None:
    """Rejects invalid parser safety limits."""
    with pytest.raises(ValueError, match="max_query_length"):
        ParseLimits(max_query_length=0)


def test_parser_uses_shared_default_limits_instance() -> None:
    """Reuses the shared default limits on the common parse path."""
    parser = Parser("name==demo")
    assert parser.limits is DEFAULT_PARSE_LIMITS


def test_logical_node_rejects_single_child() -> None:
    """Prevents invalid logical AST nodes."""
    comparison = Parser("name==demo").parse()
    assert isinstance(comparison, ComparisonNode)
    with pytest.raises(ValueError, match="at least two child expressions"):
        LogicalNode(
            span=comparison.span,
            operator=LogicalOperator.AND,
            children=(comparison,),
        )
