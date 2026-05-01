"""Shared backend contracts."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Protocol


class CompiledQuery(Protocol):
    """Protocol implemented by backend-specific compiled query objects."""

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies a compiled query to a backend-specific target."""


class Backend(ABC):
    """Abstract backend contract used by the pyrsql public API."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the stable backend name."""

    @abstractmethod
    def compile_query(self, query: "Query") -> CompiledQuery:
        """Compiles a high-level query into a backend-specific form."""


from pyrsql.core.query import Query
