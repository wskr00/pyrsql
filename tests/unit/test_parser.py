"""Unit tests for the pyrsql parser."""

from pyrsql.parsing.ast import ComparisonNode
from pyrsql.parsing.ast import LogicalNode
from pyrsql.parsing.ast import LogicalOperator
from pyrsql.parsing.errors import ParseError
from pyrsql.parsing.limits import ParseLimits
from pyrsql.parsing.parser import Parser


def test_parser_builds_comparison_node() -> None:
    """Parses a simple comparison."""
    expression = Parser("name==demo").parse()
    assert isinstance(expression, ComparisonNode)
    assert expression.selector == "name"
    assert expression.operator.name == "equal"
    assert tuple(argument.text for argument in expression.arguments) == ("demo",)


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


def test_parser_allows_nullary_null_check() -> None:
    """Allows null-check operators without explicit arguments."""
    expression = Parser("company.code=na=").parse()
    assert isinstance(expression, ComparisonNode)
    assert expression.operator.name == "is_null"
    assert expression.arguments == ()


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
