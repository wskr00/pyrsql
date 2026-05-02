"""Semantic nodes for shared pyrsql selectors."""

from dataclasses import dataclass
from typing import TypeAlias

from pyrsql.selector.ast import SelectorLiteral


@dataclass(frozen=True, slots=True)
class SemanticColumnSelector:
    """Column-path selector after semantic normalization."""

    selector: str
    field_path: str


@dataclass(frozen=True, slots=True)
class SemanticLiteralSelector:
    """Static literal selector after semantic normalization."""

    value: SelectorLiteral


@dataclass(frozen=True, slots=True)
class SemanticFunctionSelector:
    """Function selector after semantic normalization."""

    function_name: str
    arguments: tuple["SemanticSelector", ...]


SemanticSelector: TypeAlias = (
    SemanticColumnSelector | SemanticLiteralSelector | SemanticFunctionSelector
)
