# API Reference

## Public API

::: pyrsql
    options:
      members:
        - parse
        - compile
        - apply
        - Query
        - Sort
        - PageRequest
        - QueryOptions
        - SortOptions
        - JSONOptions
        - JSONSortScalarType
        - JSONPath
        - JSONPathComparison
        - JSONScalarNormalizer
        - JSONScalarValue
        - CustomPredicateDefinition
        - FieldPolicySet
        - FieldValueConverterSet
        - ProcedureAccessPolicy
        - ValueConverter
        - ValueConverterRegistry
        - JoinHint
        - ORM
        - DEFAULT_JSON_OPTIONS

## Subpackages

- `pyrsql.adapters.fastapi` - FastAPI adapter (FastAPICriteriaConfig, RequestCriteria, CriteriaDependency)
- `pyrsql.integrations.fastapi` - FastAPI + SQLAlchemy (FastAPISQLAlchemyIntegration, FastAPISQLAlchemyResource)
- `pyrsql.orms.sqlalchemy` - SQLAlchemy backend (SQLAlchemyORM)
- `pyrsql.core` - ORM-neutral core types and options
- `pyrsql.parsing` - Lexer, parser, operators, limits
- `pyrsql.selector` - Selector syntax
- `pyrsql.semantic` - Semantic binding
- `pyrsql.sorting` - Sort syntax and binding
