"""Unit tests for the pyrsql parser."""

from __future__ import annotations

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
from pyrsql.selector.ast import FieldSelector, FunctionSelector, LiteralSelector


@pytest.mark.parametrize(
    ("source", "selector_path", "operator_name", "expected_arguments"),
    [
        pytest.param(
            "name==demo",
            "name",
            "equal",
            ("demo",),
            id="basic-comparison",
        ),
        pytest.param(
            "company.code=na=",
            "company.code",
            "is_null",
            (),
            id="null-check",
        ),
        pytest.param(
            "id=in=(1,2,3)",
            "id",
            "in",
            ("1", "2", "3"),
            id="argument-list",
        ),
    ],
)
def test_parser_builds_comparison_nodes(
    source: str,
    selector_path: str,
    operator_name: str,
    expected_arguments: tuple[str, ...],
) -> None:
    """Parses comparison expressions into comparison AST nodes."""
    expression = Parser(source).parse()

    assert isinstance(expression, ComparisonNode)
    assert isinstance(expression.selector, FieldSelector)
    assert expression.selector.raw_path == selector_path
    assert expression.operator.name == operator_name
    assert tuple(argument.text for argument in expression.arguments) == (
        expected_arguments
    )


def test_parser_preserves_and_or_precedence() -> None:
    """Parses AND more tightly than OR."""
    expression = Parser("name==demo,city==sp;age=ge=18").parse()

    assert isinstance(expression, LogicalNode)
    assert expression.operator is LogicalOperator.OR
    assert isinstance(expression.children[0], ComparisonNode)
    assert isinstance(expression.children[1], LogicalNode)
    assert expression.children[1].operator is LogicalOperator.AND


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


def test_parser_accepts_custom_operator_registry() -> None:
    """Parses custom operators registered through the parser."""
    all_match = ComparisonOperator(
        name="all_match",
        spellings=("=all=",),
        minimum_arguments=1,
        maximum_arguments=1,
    )
    registry = OperatorRegistry(
        operators=DEFAULT_OPERATOR_REGISTRY.operators + (all_match,),
    )

    expression = Parser(
        "name=all=demo",
        operator_registry=registry,
    ).parse()

    assert isinstance(expression, ComparisonNode)
    assert expression.operator.name == "all_match"


@pytest.mark.parametrize(
    ("source", "limits", "pattern"),
    [
        pytest.param(
            "name==",
            None,
            r"expects at least",
            id="missing-required-argument",
        ),
        pytest.param(
            "((name==demo))",
            ParseLimits(max_expression_depth=2),
            r"maximum supported expression depth",
            id="depth-limit",
        ),
    ],
)
def test_parser_rejects_invalid_query_shapes(
    source: str,
    limits: ParseLimits | None,
    pattern: str,
) -> None:
    """Rejects invalid parse shapes through structured parse errors."""
    with pytest.raises(ParseError, match=pattern):
        Parser(source, limits=limits).parse()


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
