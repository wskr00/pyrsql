"""High-level sort object."""

from dataclasses import dataclass
from typing import Any

from pyrsql.core.compiler import SortCompilationResult
from pyrsql.core.options import SortOptions
from pyrsql.orms.base import ORM
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
    """Represents an ORM-neutral parsed sort request.

    Attributes:
        text: Raw sort text used to build the request.
        options: Normalized sort configuration used during parsing.
        fields: Parsed sort fields, if parsing succeeded.
        semantic_fields: Semantic sort fields, if analysis succeeded.
    """

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
        """Parses raw sort text into a sort object.

        Args:
            sort_text: Raw sort text to parse.
            options: Optional sort configuration.

        Returns:
            A parsed sort object.
        """
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
        """Parses raw sort text into sort fields.

        Args:
            sort_text: Raw sort text to parse.
            options: Sort configuration used by the parser.

        Returns:
            The parsed sort fields.
        """
        return _parse_sort_fields(sort_text, options=options)

    @staticmethod
    def analyze_fields(
        fields: tuple[SortField, ...],
        *,
        options: SortOptions,
    ) -> tuple[SemanticSortField, ...]:
        """Analyzes sort fields into semantic sort fields.

        Args:
            fields: Parsed sort fields to analyze.
            options: Sort configuration used by semantic analysis.

        Returns:
            The semantic sort fields.
        """
        return _analyze_sort_fields(fields, options=options)

    def compile(self, *, orm: ORM) -> SortCompilationResult:
        """Compiles the sort using the provided ORM.

        Args:
            orm: ORM adapter used to compile the sort.

        Returns:
            The ORM-specific sort compilation result.
        """
        compiled_sort = orm.compile_sort(self)
        return SortCompilationResult(
            orm_name=orm.name,
            compiled_sort=compiled_sort,
        )

    def apply(
        self,
        target: Any,
        model: type[Any],
        *,
        orm: ORM,
    ) -> Any:
        """Compiles and applies the sort using the provided ORM.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the sort.
            orm: ORM adapter used to compile the sort.

        Returns:
            The value returned by the ORM-specific apply operation.
        """
        return self.compile(orm=orm).apply(target=target, model=model)
