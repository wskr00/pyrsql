"""ORM-neutral JSON query models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from pyrsql.core.json.values import (
    DEFAULT_JSON_SCALAR_NORMALIZER,
    JSONScalarValue,
)

if TYPE_CHECKING:
    from pyrsql.core.json.path import JSONPath
    from pyrsql.core.json.values import (
        JSONScalarNormalizer,
    )

RawJSONArgument = tuple[str, bool]


class JSONPathComparison(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Represents one JSON path comparison after semantic normalization."""

    path: JSONPath
    operator_name: str
    values: tuple[JSONScalarValue, ...]

    @classmethod
    def from_raw_arguments(
        cls,
        *,
        path: JSONPath,
        operator_name: str,
        raw_arguments: tuple[RawJSONArgument, ...],
        normalizer: JSONScalarNormalizer | None = None,
    ) -> JSONPathComparison:
        """Builds a normalized JSON comparison from raw RSQL arguments.

        Returns:
            One normalized JSON path comparison.
        """
        value_normalizer = (
            DEFAULT_JSON_SCALAR_NORMALIZER
            if normalizer is None
            else normalizer
        )
        return cls(
            path=path,
            operator_name=operator_name,
            values=tuple(
                value_normalizer.normalize(raw_value, quoted=quoted)
                for raw_value, quoted in raw_arguments
            ),
        )
