"""High-level sort object."""

from dataclasses import dataclass
from typing import Any

from pyrsql.backends.base import Backend
from pyrsql.core.compiler import SortCompilationResult
from pyrsql.core.options import SortOptions
from pyrsql.sorting.analyzer import SortAnalyzer
from pyrsql.sorting.ast import SortField
from pyrsql.sorting.parser import SortParser
from pyrsql.sorting.semantic import SemanticSortField

_DEFAULT_SORT_OPTIONS = SortOptions()


def _resolve_sort_options(
    options: SortOptions | None,
) -> SortOptions:
    """Returns the provided options or the shared immutable default."""
    return options or _DEFAULT_SORT_OPTIONS


def _parse_sort_fields(
    sort_text: str | None,
    *,
    options: SortOptions,
) -> tuple[SortField, ...]:
    """Parses raw sort text into sort fields."""
    return SortParser(
        sort_text,
        limits=options.sort_limits,
    ).parse()


def _analyze_sort_fields(
    fields: tuple[SortField, ...],
    *,
    options: SortOptions,
) -> tuple[SemanticSortField, ...]:
    """Analyzes sort fields into semantic sort fields."""
    return SortAnalyzer(options).analyze(fields)


@dataclass(frozen=True, slots=True)
class Sort:
    """Represents a backend-neutral parsed sort request."""

    text: str | None
    options: SortOptions
    fields: tuple[SortField, ...] = ()
    semantic_fields: tuple[SemanticSortField, ...] = ()

    @classmethod
    def parse(
        cls,
        sort_text: str | None,
        *,
        options: SortOptions | None = None,
    ) -> "Sort":
        """Creates a sort object from raw sort text."""
        resolved_options = _resolve_sort_options(options)
        fields = cls.parse_fields(sort_text, options=resolved_options)
        semantic_fields = cls.analyze_fields(fields, options=resolved_options)
        return cls(
            text=sort_text,
            options=resolved_options,
            fields=fields,
            semantic_fields=semantic_fields,
        )

    @staticmethod
    def parse_fields(
        sort_text: str | None,
        *,
        options: SortOptions,
    ) -> tuple[SortField, ...]:
        """Parses raw sort text into sort fields."""
        return _parse_sort_fields(sort_text, options=options)

    @staticmethod
    def analyze_fields(
        fields: tuple[SortField, ...],
        *,
        options: SortOptions,
    ) -> tuple[SemanticSortField, ...]:
        """Analyzes sort fields into semantic sort fields."""
        return _analyze_sort_fields(fields, options=options)

    def compile(self, *, backend: Backend) -> SortCompilationResult:
        """Compiles the sort using the provided backend."""
        compiled_sort = backend.compile_sort(self)
        return SortCompilationResult(
            backend_name=backend.name,
            compiled_sort=compiled_sort,
        )

    def apply(
        self,
        target: Any,
        model: type[Any],
        *,
        backend: Backend,
    ) -> Any:
        """Compiles and applies the sort using the provided backend."""
        return self.compile(backend=backend).apply(target=target, model=model)
