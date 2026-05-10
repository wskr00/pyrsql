"""Shared ORM contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from pyrsql.core.page import PageRequest
    from pyrsql.core.query import Query
    from pyrsql.core.sort import Sort

_TargetT = TypeVar("_TargetT")
_ModelT = TypeVar("_ModelT")


class CompiledQuery(Protocol):
    """Protocol implemented by ORM-specific compiled query objects."""

    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT:
        """Applies a compiled query to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the query.

        Returns:
            The value returned by the compiled query application.
        """


class CompiledSort(Protocol):
    """Protocol implemented by ORM-specific compiled sort objects."""

    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT:
        """Applies a compiled sort to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the sort.

        Returns:
            The value returned by the compiled sort application.
        """


class CompiledPageRequest(Protocol):
    """Protocol implemented by ORM-specific compiled page objects."""

    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT:
        """Applies a compiled page request to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the page request.

        Returns:
            The value returned by the compiled page application.
        """


class ORM(ABC):
    """Abstract ORM contract used by the pyrsql public API."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The stable ORM name.

        Returns:
            The ORM's stable identifier.
        """

    @abstractmethod
    def compile_query(self, query: Query) -> CompiledQuery:
        """Compiles a high-level query into an ORM-specific form.

        Args:
            query: High-level query to compile.

        Returns:
            A compiled query object for this ORM.
        """

    @abstractmethod
    def compile_sort(self, sort: Sort) -> CompiledSort:
        """Compiles a high-level sort into an ORM-specific form.

        Args:
            sort: High-level sort request to compile.

        Returns:
            A compiled sort object for this ORM.
        """

    @abstractmethod
    def compile_page_request(
        self,
        page_request: PageRequest,
    ) -> CompiledPageRequest:
        """Compiles a pagination request into an ORM-specific form.

        Args:
            page_request: Pagination request to compile.

        Returns:
            A compiled page request object for this ORM.
        """
