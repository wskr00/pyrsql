"""FastAPI adapter for pyrsql request extraction and error translation."""

from pyrsql.adapters.fastapi.config import FastAPICriteriaConfig
from pyrsql.adapters.fastapi.criteria import RequestCriteria
from pyrsql.adapters.fastapi.dependency import (
    CriteriaDependency,
    criteria_dependency,
)

__all__ = (
    "CriteriaDependency",
    "FastAPICriteriaConfig",
    "RequestCriteria",
    "criteria_dependency",
)
