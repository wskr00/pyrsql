"""Public package interface for pyrsql."""

# pylint: disable=redefined-builtin

import pyrsql.api as api
from pyrsql.backends.base import Backend
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.compiler import PageCompilationResult
from pyrsql.core.compiler import SortCompilationResult
from pyrsql.core.conversion import FieldValueConverterSet
from pyrsql.core.conversion import ValueConverter
from pyrsql.core.conversion import ValueConverterRegistry
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.core.json.options import JSONOptions
from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import JSONScalarNormalizer
from pyrsql.core.json.values import JSONScalarValue
from pyrsql.core.page import PageRequest
from pyrsql.core.options import QueryOptions
from pyrsql.core.options import SortOptions
from pyrsql.core.procedure_policy import ProcedureAccessPolicy
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort

parse = api.parse
compile = api.compile
apply = api.apply

__all__ = [
    "Backend",
    "CompilationResult",
    "CustomPredicateDefinition",
    "FieldPolicySet",
    "FieldValueConverterSet",
    "JSONOptions",
    "JSONPath",
    "JSONPathComparison",
    "JSONScalarNormalizer",
    "JSONScalarValue",
    "PageCompilationResult",
    "PageRequest",
    "ProcedureAccessPolicy",
    "Query",
    "QueryOptions",
    "Sort",
    "SortCompilationResult",
    "SortOptions",
    "ValueConverter",
    "ValueConverterRegistry",
    "apply",
    "compile",
    "parse",
]
