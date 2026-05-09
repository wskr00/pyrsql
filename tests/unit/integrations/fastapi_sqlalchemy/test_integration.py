"""Unit tests for the FastAPI + SQLAlchemy integration helper."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import pytest
from sqlalchemy import select
from sqlalchemy.sql import Select

import pyrsql.integrations.fastapi.sqlalchemy.resource as resource_module
from pyrsql.adapters.fastapi import FastAPICriteriaConfig, RequestCriteria
from pyrsql.integrations.fastapi import (
    FastAPISQLAlchemyIntegration,
    FastAPISQLAlchemyResource,
    SQLAlchemyPaginatedSelect,
)
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

from .conftest import OtherModel, User

pytest.importorskip("fastapi")

pytestmark = [pytest.mark.unit, pytest.mark.fastapi, pytest.mark.sqlalchemy]


def test_integration_exposes_configured_criteria_dependency(
    fastapi_criteria_config: FastAPICriteriaConfig,
    sqlalchemy_orm: SQLAlchemyORM,
) -> None:
    """Returns a FastAPI criteria dependency using the stored config."""
    integration = FastAPISQLAlchemyIntegration(
        orm=sqlalchemy_orm,
        criteria_config=fastapi_criteria_config,
    )

    dependency = integration.criteria_dependency()

    assert dependency.config is fastapi_criteria_config


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {"orm": "invalid"},
            "orm must be a SQLAlchemyORM",
            id="invalid-orm",
        ),
        pytest.param(
            {"criteria_config": "invalid"},
            "criteria_config must be a FastAPICriteriaConfig",
            id="invalid-criteria-config",
        ),
    ],
)
def test_integration_rejects_invalid_public_configuration(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """Rejects invalid ORM and criteria config objects."""
    with pytest.raises(TypeError, match=pattern):
        FastAPISQLAlchemyIntegration(**cast(Any, kwargs))


def test_resource_rejects_invalid_integration_type() -> None:
    """Rejects invalid integration objects for declarative resources."""
    with pytest.raises(TypeError, match="integration must be"):
        FastAPISQLAlchemyResource(
            integration=cast(Any, object()),
            model=User,
            criteria_config=FastAPICriteriaConfig(),
        )


def test_integration_reuses_cached_dependencies(
    integration: FastAPISQLAlchemyIntegration,
) -> None:
    """Reuses dependency objects for the same model and integration."""
    assert (
        integration.criteria_dependency() is integration.criteria_dependency()
    )
    assert integration.select_dependency(User) is integration.select_dependency(
        User
    )
    assert integration.count_select_dependency(
        User
    ) is integration.count_select_dependency(User)
    assert integration.paginated_select_dependency(
        User
    ) is integration.paginated_select_dependency(User)


def test_integration_apply_delegates_to_request_criteria(
    integration: FastAPISQLAlchemyIntegration,
    base_statement: Select[Any],
    query_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Delegates apply() to RequestCriteria.apply with the configured ORM."""
    expected = object()
    calls: list[tuple[object, type[Any], SQLAlchemyORM]] = []

    def fake_apply(
        self: RequestCriteria,
        target: object,
        model: type[Any],
        *,
        orm: SQLAlchemyORM,
    ) -> object:
        assert self is query_criteria
        calls.append((target, model, orm))
        return expected

    monkeypatch.setattr(RequestCriteria, "apply", fake_apply)

    applied = integration.apply(base_statement, User, query_criteria)

    assert applied is expected
    assert calls == [(base_statement, User, integration.orm)]


def test_integration_select_builds_sorted_and_paged_select(
    integration: FastAPISQLAlchemyIntegration,
    full_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds a select through filtered and sort/page stages."""
    filtered_statement = select(User).where(User.id > 10)
    final_statement = select(User).order_by(User.name.desc())

    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "_filtered_select",
        lambda self, model, criteria: filtered_statement,
    )
    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "_apply_sort_and_page",
        lambda self, statement, model, criteria: final_statement,
    )

    statement = integration.select(User, full_criteria)

    assert statement is final_statement


def test_integration_count_select_uses_filtered_select_only(
    integration: FastAPISQLAlchemyIntegration,
    full_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds a count statement from the filtered statement only."""
    filtered_statement = select(User).where(User.id > 10)
    count_statement = select(User.id)

    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "_filtered_select",
        lambda self, model, criteria: filtered_statement,
    )
    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "_count_from_filtered_select",
        lambda self, statement: count_statement,
    )

    statement = integration.count_select(User, full_criteria)

    assert statement is count_statement


def test_integration_paginated_select_builds_bundle_from_shared_filtered_select(
    integration: FastAPISQLAlchemyIntegration,
    full_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds list and count statements from one filtered select."""
    filtered_statement = select(User).where(User.id > 10)
    list_statement = select(User).order_by(User.name.desc())
    count_statement = select(User.id)

    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "_filtered_select",
        lambda self, model, criteria: filtered_statement,
    )
    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "_apply_sort_and_page",
        lambda self, statement, model, criteria: list_statement,
    )
    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "_count_from_filtered_select",
        lambda self, statement: count_statement,
    )

    bundle = integration.paginated_select(User, full_criteria)

    assert isinstance(bundle, SQLAlchemyPaginatedSelect)
    assert bundle.statement is list_statement
    assert bundle.count_statement is count_statement


def test_integration_builds_declarative_resource(
    integration: FastAPISQLAlchemyIntegration,
) -> None:
    """Builds a route-ready declarative resource object."""
    resource = integration.resource(
        User,
        filterable_fields={"name"},
        sortable_fields={"name"},
        default_sort="name,desc",
        max_page_size=50,
        filter_examples={
            "by_name": {"summary": "By name", "value": "name==demo"}
        },
    )

    assert isinstance(resource, FastAPISQLAlchemyResource)
    assert resource.criteria_config.query_options.field_whitelist == {"name"}
    assert resource.criteria_config.sort_options.field_whitelist == {"name"}
    assert resource.criteria_config.max_page_size == 50
    assert (
        resource.criteria_config.filter_openapi_examples["by_name"]["value"]
        == "name==demo"
    )
    assert (
        resource.criteria_config.sort_openapi_examples["default_sort"]["value"]
        == "name,desc"
    )


def test_resource_generates_automatic_examples(
    integration: FastAPISQLAlchemyIntegration,
) -> None:
    """Generates filter and sort examples from declarative config."""
    resource = integration.resource(
        User,
        filterable_fields={"id", "name"},
        sortable_fields={"name"},
        default_sort="-name",
    )

    assert (
        resource.criteria_config.filter_openapi_examples["filter_by_id"][
            "value"
        ]
        == "id==1"
    )
    assert (
        resource.criteria_config.filter_openapi_examples["filter_by_name"][
            "value"
        ]
        == "name==demo"
    )
    assert (
        resource.criteria_config.sort_openapi_examples["sort_by_name_asc"][
            "value"
        ]
        == "name,asc"
    )
    assert (
        resource.criteria_config.sort_openapi_examples["default_sort"]["value"]
        == "name,desc"
    )


def test_resource_applies_default_sort_when_request_sort_is_absent(
    integration: FastAPISQLAlchemyIntegration,
) -> None:
    """Injects the declarative default sort into request criteria."""
    resource = integration.resource(User, default_sort="-name")

    criteria = resource.criteria_dependency()(RequestCriteria())

    assert criteria.sort is not None
    assert criteria.sort.text == "name,desc"


def test_resource_applier_wraps_integration_apply(
    integration: FastAPISQLAlchemyIntegration,
    full_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds a callable that delegates to integration.apply()."""
    resource = integration.resource(User)
    base_statement = select(User)
    expected_statement = select(User).where(User.id > 10)
    calls: list[tuple[Select[Any], type[Any], RequestCriteria]] = []

    def fake_apply(
        statement: Select[Any],
        model: type[Any],
        criteria: RequestCriteria,
    ) -> Select[Any]:
        calls.append((statement, model, criteria))
        return expected_statement

    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "apply",
        lambda self, statement, model, criteria: fake_apply(
            statement,
            model,
            criteria,
        ),
    )

    applied = resource.applier(full_criteria)(base_statement)

    assert applied is expected_statement
    assert calls == [(base_statement, User, full_criteria)]


def test_resource_count_select_uses_query_only_stage(
    integration: FastAPISQLAlchemyIntegration,
    full_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds counts from the query stage without sort/page lowering."""
    resource = integration.resource(User)
    filtered_statement = select(User).where(User.id > 10)
    count_statement = select(User.id)
    calls: list[
        tuple[Select[Any], type[Any], RequestCriteria, SQLAlchemyORM]
    ] = []

    def fake_apply_query_with_orm(
        statement: Select[Any],
        model: type[Any],
        criteria: RequestCriteria,
        orm: SQLAlchemyORM,
    ) -> Select[Any]:
        calls.append((statement, model, criteria, orm))
        return filtered_statement

    monkeypatch.setattr(
        resource_module,
        "apply_query_with_orm",
        fake_apply_query_with_orm,
    )
    monkeypatch.setattr(
        resource_module,
        "count_from_filtered_select",
        lambda statement: count_statement,
    )

    statement = resource.count_select(full_criteria)

    assert statement is count_statement
    assert calls[0][1:] == (User, full_criteria, integration.orm)


def test_resource_paginated_select_uses_shared_filtered_select(
    integration: FastAPISQLAlchemyIntegration,
    full_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Builds list and count statements from one filtered base statement."""
    resource = integration.resource(User)
    filtered_statement = select(User).where(User.id > 10)
    list_statement = select(User).order_by(User.name.desc())
    count_statement = select(User.id)

    monkeypatch.setattr(
        resource_module,
        "apply_query_with_orm",
        lambda statement, model, criteria, orm: filtered_statement,
    )
    monkeypatch.setattr(
        resource_module,
        "apply_sort_and_page_with_orm",
        lambda statement, model, criteria, orm: list_statement,
    )
    monkeypatch.setattr(
        resource_module,
        "count_from_filtered_select",
        lambda statement: count_statement,
    )

    bundle = resource.paginated_select(full_criteria)

    assert bundle.statement is list_statement
    assert bundle.count_statement is count_statement


def test_resource_select_uses_statement_factory_for_base_statement(
    integration: FastAPISQLAlchemyIntegration,
    query_criteria: RequestCriteria,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uses a custom base statement when configured."""
    statement = select(User).where(User.id > 10)
    expected_statement = select(User).where(User.name == "demo")
    resource = integration.resource(
        User,
        statement_factory=lambda: statement,
    )

    calls: list[tuple[Select[Any], type[Any], RequestCriteria]] = []

    def fake_apply(
        integration_helper: FastAPISQLAlchemyIntegration,
        base_statement: Select[Any],
        model: type[Any],
        criteria: RequestCriteria,
    ) -> Select[Any]:
        del integration_helper
        calls.append((base_statement, model, criteria))
        return expected_statement

    monkeypatch.setattr(
        FastAPISQLAlchemyIntegration,
        "apply",
        fake_apply,
    )

    assert resource.select(query_criteria) is expected_statement
    assert calls == [(statement, User, query_criteria)]


@pytest.mark.parametrize(
    ("statement_factory", "pattern"),
    [
        pytest.param(
            lambda: cast(Any, "invalid"),
            r"sqlalchemy\.sql\.Select",
            id="non-select-result",
        ),
        pytest.param(
            lambda: select(OtherModel),
            "statement_factory must return a Select compatible",
            id="wrong-model",
        ),
    ],
)
def test_resource_rejects_invalid_statement_factory_results(
    integration: FastAPISQLAlchemyIntegration,
    statement_factory: Callable[[], object],
    pattern: str,
) -> None:
    """Rejects invalid base statement factories for declarative resources."""
    resource = integration.resource(
        User,
        statement_factory=cast(Callable[[], Select[Any]], statement_factory),
    )

    with pytest.raises(TypeError, match=pattern):
        resource.select(RequestCriteria())


def test_resource_reuses_integration_cached_base_select(
    integration: FastAPISQLAlchemyIntegration,
) -> None:
    """Reuses the integration cached base select on the common path."""
    resource = integration.resource(User)

    assert resource.select(RequestCriteria()) is integration.base_select(User)


def test_resource_reuses_cached_dependencies(
    integration: FastAPISQLAlchemyIntegration,
) -> None:
    """Reuses dependency objects created by a declarative resource."""
    resource = integration.resource(User, default_sort="-name")

    assert resource.applier_dependency() is resource.applier_dependency()
    assert resource.select_dependency() is resource.select_dependency()
    assert (
        resource.count_select_dependency() is resource.count_select_dependency()
    )
    assert (
        resource.paginated_select_dependency()
        is resource.paginated_select_dependency()
    )


@pytest.mark.parametrize(
    "method_name",
    ["select", "count_select", "paginated_select"],
)
def test_integration_rejects_invalid_request_criteria(
    integration: FastAPISQLAlchemyIntegration,
    method_name: str,
) -> None:
    """Rejects non-RequestCriteria values at public entrypoints."""
    method = getattr(integration, method_name)

    with pytest.raises(TypeError, match="criteria must be a RequestCriteria"):
        method(User, cast(Any, "invalid"))


def test_paginated_select_rejects_invalid_statements() -> None:
    """Rejects non-select statement payloads in the paginated bundle."""
    with pytest.raises(TypeError):
        SQLAlchemyPaginatedSelect(
            statement=cast(Any, "invalid"),
            count_statement=select(User),
        )


def test_resource_dependency_respects_explicit_max_page_size(
    integration: FastAPISQLAlchemyIntegration,
) -> None:
    """Uses the resource-specific max page size when explicitly provided."""
    resource = integration.resource(User, max_page_size=50)

    assert resource.criteria_config.max_page_size == 50
