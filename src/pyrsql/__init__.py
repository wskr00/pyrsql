"""Public package interface for pyrsql."""

import pyrsql.api as api
from pyrsql.backends.base import Backend
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.core.query import Query

parse = api.parse
compile = api.compile
apply = api.apply

__all__ = [
    "Backend",
    "CompilationResult",
    "Query",
    "QueryOptions",
    "apply",
    "compile",
    "parse",
]
