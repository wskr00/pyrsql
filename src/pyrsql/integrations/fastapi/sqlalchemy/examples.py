"""OpenAPI example generation helpers for FastAPI SQLAlchemy resources."""

_DEFAULT_STRING_EXAMPLE = "demo"
_DEFAULT_NUMERIC_EXAMPLE = 1
_DEFAULT_DATE_EXAMPLE = "2026-01-01"


def normalize_default_sort(default_sort: str) -> str:
    """Normalizes shorthand default sort expressions.

    Returns:
        The normalized default sort expression.

    Raises:
        ValueError: If the provided default sort is blank.
    """
    stripped = default_sort.strip()
    if not stripped:
        raise ValueError("default_sort must not be blank.")
    if "," in stripped:
        return stripped
    if stripped.startswith("-") and len(stripped) > 1:
        return f"{stripped[1:]},desc"
    if stripped.startswith("+") and len(stripped) > 1:
        return f"{stripped[1:]},asc"
    return stripped


def field_example_value(field_path: str) -> str | int:
    """Builds a simple example value from a field path.

    Returns:
        A simple scalar example value inferred from the field path.
    """
    normalized = field_path.lower()
    if normalized == "id" or normalized.endswith((".id", "_id")):
        return _DEFAULT_NUMERIC_EXAMPLE
    if any(
        token in normalized
        for token in ("date", "time", "created_at", "updated_at")
    ):
        return _DEFAULT_DATE_EXAMPLE
    return _DEFAULT_STRING_EXAMPLE


def format_filter_example(field_path: str) -> str:
    """Formats one automatic filter example.

    Returns:
        One automatic filter expression example.
    """
    value = field_example_value(field_path)
    return f"{field_path}=={value}"


def build_filter_examples(
    filterable_fields: set[str] | frozenset[str] | None,
) -> dict[str, dict[str, object]]:
    """Builds automatic filter examples from declarative field config.

    Returns:
        Automatic OpenAPI examples for filter parameters.
    """
    if not filterable_fields:
        return {}
    examples: dict[str, dict[str, object]] = {}
    for field_path in sorted(filterable_fields)[:3]:
        key = field_path.replace(".", "_")
        examples[f"filter_by_{key}"] = {
            "summary": f"Filter by {field_path}",
            "value": format_filter_example(field_path),
        }
    return examples


def build_sort_examples(
    sortable_fields: set[str] | frozenset[str] | None,
    default_sort: str | None,
) -> dict[str, dict[str, object]]:
    """Builds automatic sort examples from declarative sort config.

    Returns:
        Automatic OpenAPI examples for sort parameters.
    """
    examples: dict[str, dict[str, object]] = {}
    if sortable_fields:
        first_field = min(sortable_fields)
        example_key = first_field.replace(".", "_")
        examples[f"sort_by_{example_key}_asc"] = {
            "summary": f"Sort by {first_field} ascending",
            "value": f"{first_field},asc",
        }
    if default_sort is not None:
        examples["default_sort"] = {
            "summary": "Default sort",
            "value": normalize_default_sort(default_sort),
        }
    return examples


def merge_openapi_examples(
    generated: dict[str, dict[str, object]],
    explicit: dict[str, dict[str, object]] | None,
) -> dict[str, dict[str, object]]:
    """Merges automatic and explicit OpenAPI examples.

    Returns:
        The merged OpenAPI example mapping.
    """
    if not explicit:
        return generated
    merged = dict(generated)
    merged.update(explicit)
    return merged
