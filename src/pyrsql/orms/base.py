"""Shared ORM contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeAlias

from pyrsql.core.compiler import CompiledArtifact

if TYPE_CHECKING:
    from pyrsql.core.page import PageRequest
    from pyrsql.core.query import Query
    from pyrsql.core.sort import Sort

CompiledQuery: TypeAlias = CompiledArtifact
CompiledSort: TypeAlias = CompiledArtifact
CompiledPageRequest: TypeAlias = CompiledArtifact


class ORMError(ValueError):
    """Base exception for ORM backend failures."""

    code: ClassVar[str] = "orm_error"


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
