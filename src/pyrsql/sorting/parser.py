"""Parser for pyrsql sort expressions."""

from typing import Final

from pyrsql.selector.ast import Selector
from pyrsql.selector.parser import DEFAULT_SELECTOR_PARSER, SelectorParseError
from pyrsql.sorting.ast import SortDirection, SortField
from pyrsql.sorting.errors import SortParseError
from pyrsql.sorting.limits import DEFAULT_SORT_LIMITS, SortLimits

_EMPTY_FIELDS: Final[tuple[SortField, ...]] = ()


class SortParser:
    """Parses sort expressions into orm-neutral field descriptors."""

    def __init__(
        self,
        source: str | None,
        *,
        limits: SortLimits | None = None,
    ) -> None:
        self._source = (source or "").strip()
        self._limits = limits or DEFAULT_SORT_LIMITS
        self._selector_parser = DEFAULT_SELECTOR_PARSER

    def parse(self) -> tuple[SortField, ...]:
        """Parses the configured sort expression."""
        if not self._source:
            return _EMPTY_FIELDS

        max_sort_length = self._limits.max_sort_length
        max_fields = self._limits.max_fields
        if len(self._source) > max_sort_length:
            raise SortParseError(
                "Sort expression exceeds the maximum supported length of "
                f"{max_sort_length}."
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
                    f"count of {max_fields}."
                )
        return tuple(fields)

    def _parse_clause(
        self,
        clause: str,
        *,
        clause_index: int,
    ) -> SortField | None:
        """Parses a single semicolon-delimited sort clause."""
        try:
            parts = list(
                self._selector_parser.split_top_level(
                    clause,
                    delimiter=",",
                )
            )
        except SelectorParseError as error:
            raise SortParseError(str(error)) from error
        if not parts:
            return None
        if len(parts) > 3:
            raise SortParseError(
                "Sort clause "
                f"#{clause_index} {clause!r} has too many comma-separated "
                "parts."
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
        if len(parts) > 2:
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

    def _parse_direction(
        self,
        raw_direction: str,
        clause: str,
        *,
        clause_index: int,
    ) -> SortDirection:
        """Parses the direction token for a sort clause."""
        direction = SortDirection.from_raw(raw_direction)
        if direction is not None:
            return direction
        raise SortParseError(
            f"Sort clause #{clause_index} {clause!r} has unsupported direction "
            f"{raw_direction!r}."
        )

    def _parse_ignore_case(
        self,
        raw_flag: str,
        clause: str,
        *,
        clause_index: int,
    ) -> bool:
        """Parses the ignore-case modifier for a sort clause."""
        match raw_flag.lower():
            case "ic":
                return True
            case _:
                raise SortParseError(
                    f"Sort clause #{clause_index} {clause!r} has unsupported "
                    "modifier "
                    f"{raw_flag!r}."
                )

    def _parse_selector(
        self,
        raw_selector: str,
        *,
        clause_index: int,
    ) -> Selector:
        """Parses a sort selector recursively."""
        try:
            return self._selector_parser.parse(
                raw_selector,
                max_length=self._limits.max_field_path_length,
                context=f"Sort selector in clause #{clause_index}",
            )
        except SelectorParseError as error:
            raise SortParseError(str(error)) from error
