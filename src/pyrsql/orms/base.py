"""Shared ORM contracts."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pyrsql.core.page import PageRequest
    from pyrsql.core.query import Query
    from pyrsql.core.sort import Sort


class CompiledQuery(Protocol):
    """Protocol implemented by ORM-specific compiled query objects."""

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies a compiled query to an ORM-specific target."""


class CompiledSort(Protocol):
    """Protocol implemented by ORM-specific compiled sort objects."""

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies a compiled sort to an ORM-specific target."""


class CompiledPageRequest(Protocol):
    """Protocol implemented by ORM-specific compiled page objects."""

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies a compiled page request to an ORM-specific target."""


class ORM(ABC):
    """Abstract ORM contract used by the pyrsql public API."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the stable ORM name."""

    @abstractmethod
    def compile_query(self, query: "Query") -> CompiledQuery:
        """Compiles a high-level query into an ORM-specific form."""

    @abstractmethod
    def compile_sort(self, sort: "Sort") -> CompiledSort:
        """Compiles a high-level sort into an ORM-specific form."""

    @abstractmethod
    def compile_page_request(
        self,
        page_request: "PageRequest",
    ) -> CompiledPageRequest:
        """Compiles a pagination request into an ORM-specific form."""
