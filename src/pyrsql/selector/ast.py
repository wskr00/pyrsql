"""AST nodes for shared pyrsql selectors."""

from dataclasses import dataclass
from typing import TypeAlias


SelectorLiteral: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class ColumnSelector:
    """Column-path selector."""

    selector: str


@dataclass(frozen=True, slots=True)
class LiteralSelector:
    """Static literal selector."""

    value: SelectorLiteral


@dataclass(frozen=True, slots=True)
class FunctionSelector:
    """Function selector."""

    function_name: str
    arguments: tuple["Selector", ...]


Selector: TypeAlias = ColumnSelector | LiteralSelector | FunctionSelector
