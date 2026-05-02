"""Shared backend contracts."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import TYPE_CHECKING
from typing import Protocol

if TYPE_CHECKING:
    from pyrsql.core.page import PageRequest
    from pyrsql.core.query import Query
    from pyrsql.core.sort import Sort


class CompiledQuery(Protocol):
    """Protocol implemented by backend-specific compiled query objects."""

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies a compiled query to a backend-specific target."""


class CompiledSort(Protocol):
    """Protocol implemented by backend-specific compiled sort objects."""

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies a compiled sort to a backend-specific target."""


class CompiledPageRequest(Protocol):
    """Protocol implemented by backend-specific compiled page objects."""

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies a compiled page request to a backend-specific target."""


class Backend(ABC):
    """Abstract backend contract used by the pyrsql public API."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the stable backend name."""

    @abstractmethod
    def compile_query(self, query: "Query") -> CompiledQuery:
        """Compiles a high-level query into a backend-specific form."""

    @abstractmethod
    def compile_sort(self, sort: "Sort") -> CompiledSort:
        """Compiles a high-level sort into a backend-specific form."""

    @abstractmethod
    def compile_page_request(
        self,
        page_request: "PageRequest",
    ) -> CompiledPageRequest:
        """Compiles a pagination request into a backend-specific form."""
