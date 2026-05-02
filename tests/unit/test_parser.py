"""Unit tests for the pyrsql parser."""

from pyrsql.parsing.ast import ComparisonNode
from pyrsql.parsing.ast import LogicalNode
from pyrsql.parsing.ast import LogicalOperator
from pyrsql.parsing.errors import ParseError
from pyrsql.parsing.limits import ParseLimits
from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.operators import OperatorRegistry
from pyrsql.parsing.parser import Parser
from pyrsql.selector.ast import ColumnSelector
from pyrsql.selector.ast import FunctionSelector
from pyrsql.selector.ast import LiteralSelector


def test_parser_builds_comparison_node() -> None:
    """Parses a simple comparison."""
    expression = Parser("name==demo").parse()
    assert isinstance(expression, ComparisonNode)
    assert isinstance(expression.selector, ColumnSelector)
    assert expression.selector.selector == "name"
    assert expression.operator.name == "equal"
    assert tuple(argument.text for argument in expression.arguments) == (
        "demo",
    )


def test_parser_preserves_and_or_precedence() -> None:
    """Parses AND more tightly than OR."""
    expression = Parser(
        "name==demo,city==sp;age=ge=18"
    ).parse()
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


def test_parser_parses_function_selector_in_comparison() -> None:
    """Parses nested function selectors in comparison expressions."""
    expression = Parser("@concat[@upper[name]|#123]==demo").parse()
    assert isinstance(expression, ComparisonNode)
    assert isinstance(expression.selector, FunctionSelector)
    assert expression.selector.function_name == "concat"
    assert isinstance(expression.selector.arguments[0], FunctionSelector)
    assert isinstance(expression.selector.arguments[1], LiteralSelector)


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
    try:
        Parser("name==").parse()
    except ParseError as error:
        assert "expects at least" in str(error)
    else:
        raise AssertionError("Expected a ParseError for missing arguments.")


def test_parser_enforces_depth_limit() -> None:
    """Rejects overly deep expressions."""
    limits = ParseLimits(max_expression_depth=2)
    try:
        Parser("((name==demo))", limits=limits).parse()
    except ParseError as error:
        assert "maximum supported expression depth" in str(error)
    else:
        raise AssertionError("Expected a ParseError for excessive depth.")
