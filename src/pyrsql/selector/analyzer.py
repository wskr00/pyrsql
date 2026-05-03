"""Shared semantic normalization for pyrsql selectors."""

from collections.abc import Callable, Mapping

from pyrsql.selector.ast import (
    ColumnSelector,
    FunctionSelector,
    LiteralSelector,
    Selector,
)
from pyrsql.selector.semantic import (
    SemanticColumnSelector,
    SemanticFunctionSelector,
    SemanticLiteralSelector,
    SemanticSelector,
)


class SelectorSemanticAnalyzer:
    """Normalizes parsed selectors into semantic selector nodes."""

    def __init__(self, field_mapping: Mapping[str, str]) -> None:
        self._field_mapping = field_mapping

    def analyze(
        self,
        selector: Selector,
        *,
        validate_field: Callable[[str], None],
        validate_function: Callable[[str], None],
    ) -> SemanticSelector:
        """Analyzes one parsed selector recursively."""
        if isinstance(selector, ColumnSelector):
            field_path = self._field_mapping.get(
                selector.selector,
                selector.selector,
            )
            validate_field(field_path)
            return SemanticColumnSelector(
                selector=selector.selector,
                field_path=field_path,
            )
        if isinstance(selector, LiteralSelector):
            return SemanticLiteralSelector(value=selector.value)
        if not isinstance(selector, FunctionSelector):
            raise TypeError("Expected FunctionSelector")
        validate_function(selector.function_name)
        return SemanticFunctionSelector(
            function_name=selector.function_name,
            arguments=tuple(
                self.analyze(
                    argument,
                    validate_field=validate_field,
                    validate_function=validate_function,
                )
                for argument in selector.arguments
            ),
        )
