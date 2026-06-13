"""Unit tests for selector AST models."""

from __future__ import annotations

from pyrsql.selector.ast import FieldSelector, FunctionSelector, LiteralSelector


def test_function_selector_walk_traverses_nested_arguments() -> None:
    """Function selectors walk nested selectors depth-first."""
    nested = FunctionSelector(
        function_name="lower",
        arguments=(
            FieldSelector(
                raw_path="user.name",
            ),
        ),
    )
    selector = FunctionSelector(
        function_name="upper",
        arguments=(nested, LiteralSelector(value="x")),
    )

    walked = tuple(selector.walk())

    assert walked == (
        selector,
        nested,
        nested.arguments[0],
        selector.arguments[1],
    )
