"""Parser for pyrsql sort expressions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pyrsql.selector.parser import DEFAULT_SELECTOR_PARSER, SelectorParseError
from pyrsql.sorting.ast import SortDirection, SortField
from pyrsql.sorting.errors import SortParseError
from pyrsql.sorting.limits import DEFAULT_SORT_LIMITS, SortLimits

if TYPE_CHECKING:
    from pyrsql.selector.ast import SelectorNode

_EMPTY_FIELDS: Final[tuple[SortField, ...]] = ()
_MAX_SORT_PARTS: Final = 3
_MIN_SORT_PARTS_FOR_IGNORE_CASE: Final = 2


class SortParser:
    """Parses sort expressions into orm-neutral field descriptors."""

    def __init__(
        self,
        source: str | None,
        *,
        limits: SortLimits | None = None,
    ) -> None:
        """Initializes the parser with raw sort text and limits."""
        self._source = self._normalize_source(source)
        self._limits = self._normalize_limits(limits)

    @staticmethod
    def _normalize_source(source: str | None) -> str:
        """Validates and normalizes raw sort source text.

        Returns:
            The stripped sort source text, or an empty string for ``None``.

        Raises:
            TypeError: If the provided source is not a string or ``None``.
        """
        if source is None:
            return ""
        if not isinstance(source, str):
            raise TypeError("Sort source must be a string or None.")
        return source.strip()

    @staticmethod
    def _normalize_limits(limits: SortLimits | None) -> SortLimits:
        """Validates and normalizes sort parser limits.

        Returns:
            The provided limits, or the shared defaults when omitted.

        Raises:
            TypeError: If the provided limits are not a ``SortLimits`` instance.
        """
        if limits is None:
            return DEFAULT_SORT_LIMITS
        if not isinstance(limits, SortLimits):
            raise TypeError("Sort limits must be a SortLimits instance.")
        return limits

    def parse(self) -> tuple[SortField, ...]:
        """Parses the configured sort expression.

        Returns:
            The parsed sort fields.

        Raises:
            SortParseError: If the expression is invalid.
        """
        if not self._source:
            return _EMPTY_FIELDS

        max_sort_length = self._limits.max_sort_length
        max_fields = self._limits.max_fields
        if len(self._source) > max_sort_length:
            raise SortParseError(
                "Sort expression exceeds the maximum supported length of "
                f"{max_sort_length}.",
            )

        fields: list[SortField] = []
        for clause_index, clause in enumerate(self._source.split(";"), start=1):
            parsed_field = self._parse_clause(clause, clause_index=clause_index)
            if parsed_field is None:
                continue
            fields.append(parsed_field)
            if len(fields) > max_fields:
                raise SortParseError(
                    "Sort expression exceeds the maximum supported field "
                    f"count of {max_fields}.",
                )
        return tuple(fields)

    def _parse_clause(
        self,
        clause: str,
        *,
        clause_index: int,
    ) -> SortField | None:
        """Parses a single semicolon-delimited sort clause.

        Returns:
            The parsed sort field, or ``None`` for blank clauses.

        Raises:
            SortParseError: If the clause syntax is invalid.
        """
        clause = clause.strip()
        if not clause:
            return None
        try:
            parts = self._split_clause_parts(
                clause,
                clause_index=clause_index,
            )
        except SelectorParseError as error:
            raise SortParseError(str(error)) from error
        if not parts:
            return None
        if len(parts) > _MAX_SORT_PARTS:
            raise SortParseError(
                "Sort clause "
                f"#{clause_index} {clause!r} has too many comma-separated "
                "parts.",
            )

        selector = self._parse_selector(parts[0], clause_index=clause_index)

        direction = SortDirection.ASCENDING
        if len(parts) > 1:
            direction = self._parse_direction(
                parts[1],
                clause,
                clause_index=clause_index,
            )

        ignore_case = False
        if len(parts) > _MIN_SORT_PARTS_FOR_IGNORE_CASE:
            ignore_case = self._parse_ignore_case(
                parts[2],
                clause,
                clause_index=clause_index,
            )

        return SortField(
            selector=selector,
            direction=direction,
            ignore_case=ignore_case,
        )

    @staticmethod
    def _split_clause_parts(
        clause: str,
        *,
        clause_index: int,
    ) -> tuple[str, ...]:
        """Splits one sort clause while rejecting empty comma parts.

        Returns:
            The normalized comma-separated parts.

        Raises:
            SortParseError: If the clause contains an empty comma part.
        """
        parts = DEFAULT_SELECTOR_PARSER.split_top_level(
            clause,
            delimiter=",",
        )
        if not parts:
            return ()

        if any(not part.strip() for part in clause.split(",")):
            raise SortParseError(
                f"Sort clause #{clause_index} {clause!r} contains empty parts.",
            )
        return parts

    @staticmethod
    def _parse_direction(
        raw_direction: str,
        clause: str,
        *,
        clause_index: int,
    ) -> SortDirection:
        """Parses the direction token for a sort clause.

        Returns:
            The parsed sort direction.

        Raises:
            SortParseError: If the direction is unsupported.
        """
        direction = SortDirection.from_raw(raw_direction.strip())
        if direction is not None:
            return direction
        raise SortParseError(
            f"Sort clause #{clause_index} {clause!r} has unsupported direction "
            f"{raw_direction!r}.",
        )

    @staticmethod
    def _parse_ignore_case(
        raw_flag: str,
        clause: str,
        *,
        clause_index: int,
    ) -> bool:
        """Parses the ignore-case modifier for a sort clause.

        Returns:
            ``True`` when the modifier enables case-insensitive sort.

        Raises:
            SortParseError: If the modifier is unsupported.
        """
        match raw_flag.strip().lower():
            case "ic":
                return True
            case _:
                raise SortParseError(
                    f"Sort clause #{clause_index} {clause!r} has unsupported "
                    "modifier "
                    f"{raw_flag!r}.",
                )

    def _parse_selector(
        self,
        raw_selector: str,
        *,
        clause_index: int,
    ) -> SelectorNode:
        """Parses a sort selector recursively.

        Returns:
            The parsed selector node.

        Raises:
            SortParseError: If the selector syntax is invalid.
        """
        try:
            return DEFAULT_SELECTOR_PARSER.parse(
                raw_selector,
                max_length=self._limits.max_field_path_length,
                context=f"Sort selector in clause #{clause_index}",
            )
        except SelectorParseError as error:
            raise SortParseError(str(error)) from error
