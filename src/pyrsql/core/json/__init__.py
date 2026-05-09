"""ORM-neutral JSON query primitives."""

from pyrsql.core.json.options import DEFAULT_JSON_OPTIONS, JSONOptions
from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import (
    DEFAULT_JSON_SCALAR_NORMALIZER,
    JSONScalarNormalizer,
    JSONScalarValue,
)

__all__ = [
    "DEFAULT_JSON_OPTIONS",
    "DEFAULT_JSON_SCALAR_NORMALIZER",
    "JSONOptions",
    "JSONPath",
    "JSONPathComparison",
    "JSONScalarNormalizer",
    "JSONScalarValue",
]
