"""Public package interface for pyrsql."""

# pylint: disable=redefined-builtin

import pyrsql.api as api
from pyrsql.backends.base import Backend
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.compiler import PageCompilationResult
from pyrsql.core.compiler import SortCompilationResult
from pyrsql.core.page import PageRequest
from pyrsql.core.options import QueryOptions
from pyrsql.core.options import SortOptions
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort

parse = api.parse
compile = api.compile
apply = api.apply

__all__ = [
    "Backend",
    "CompilationResult",
    "PageCompilationResult",
    "PageRequest",
    "Query",
    "QueryOptions",
    "Sort",
    "SortCompilationResult",
    "SortOptions",
    "apply",
    "compile",
    "parse",
]
