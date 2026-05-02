"""Backend-neutral JSON query primitives."""

from pyrsql.core.json.options import JSONOptions
from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import JSONScalarNormalizer
from pyrsql.core.json.values import JSONScalarValue

__all__ = [
    "JSONOptions",
    "JSONPath",
    "JSONPathComparison",
    "JSONScalarNormalizer",
    "JSONScalarValue",
]
