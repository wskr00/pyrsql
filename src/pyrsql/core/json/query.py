"""ORM-neutral JSON query models."""

import msgspec

from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.values import (
    DEFAULT_JSON_SCALAR_NORMALIZER,
    JSONScalarNormalizer,
    JSONScalarValue,
)


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
        raw_arguments: tuple[tuple[str, bool], ...],
        normalizer: JSONScalarNormalizer | None = None,
    ) -> "JSONPathComparison":
        """Builds a normalized JSON comparison from raw RSQL arguments."""
        value_normalizer = normalizer or DEFAULT_JSON_SCALAR_NORMALIZER
        return cls(
            path=path,
            operator_name=operator_name,
            values=tuple(
                value_normalizer.normalize(raw_value, quoted=quoted)
                for raw_value, quoted in raw_arguments
            ),
        )
