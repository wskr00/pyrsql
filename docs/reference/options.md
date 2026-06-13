# Options Reference

## QueryOptions

| Field | Type | Default |
|-------|------|---------|
| `strict_equality` | `bool` | `False` |
| `distinct` | `bool` | `False` |
| `like_escape_character` | `str \| None` | `None` |
| `field_mapping` | `Mapping[str, str]` | `{}` |
| `model_field_mapping` | `Mapping[type, Mapping[str, str]]` | `{}` |
| `join_hints` | `Mapping[str, JoinHint]` | `{}` |
| `field_whitelist` | `frozenset[str]` | `frozenset()` |
| `field_blacklist` | `frozenset[str]` | `frozenset()` |
| `model_field_whitelist` | `Mapping[type, frozenset[str]]` | `{}` |
| `model_field_blacklist` | `Mapping[type, frozenset[str]]` | `{}` |
| `procedure_whitelist` | `tuple[str, ...]` | `()` |
| `procedure_blacklist` | `tuple[str, ...]` | `()` |
| `parse_limits` | `ParseLimits` | `DEFAULT_PARSE_LIMITS` |
| `operator_registry` | `OperatorRegistry` | `DEFAULT_OPERATOR_REGISTRY` |
| `custom_predicates` | `Mapping[str, CustomPredicateDefinition]` | `{}` |
| `value_converter_registry` | `ValueConverterRegistry` | `DEFAULT_VALUE_CONVERTER_REGISTRY` |
| `field_value_converters` | `Mapping[str, ValueConverter]` | `{}` |
| `model_field_value_converters` | `Mapping[type, Mapping[str, ValueConverter]]` | `{}` |
| `json_options` | `JSONOptions` | `DEFAULT_JSON_OPTIONS` |

Notes:

- configuration containers are normalized into immutable views
- procedure allow/block rules are compiled as regex policies and evaluated with
  `fullmatch`, not partial match
- built-in scalar conversion uses `msgspec`-backed conversion paths where
  possible

## SortOptions

| Field | Type | Default |
|-------|------|---------|
| `field_mapping` | `Mapping[str, str]` | `{}` |
| `model_field_mapping` | `Mapping[type, Mapping[str, str]]` | `{}` |
| `join_hints` | `Mapping[str, JoinHint]` | `{}` |
| `field_whitelist` | `frozenset[str]` | `frozenset()` |
| `field_blacklist` | `frozenset[str]` | `frozenset()` |
| `model_field_whitelist` | `Mapping[type, frozenset[str]]` | `{}` |
| `model_field_blacklist` | `Mapping[type, frozenset[str]]` | `{}` |
| `procedure_whitelist` | `tuple[str, ...]` | `()` |
| `procedure_blacklist` | `tuple[str, ...]` | `()` |
| `sort_limits` | `SortLimits` | `DEFAULT_SORT_LIMITS` |
| `json_options` | `JSONOptions` | `DEFAULT_JSON_OPTIONS` |

Notes:

- sort field and function restrictions follow the same policy model as queries
- sort configuration is immutable and shareable across threads/tasks

## JSONOptions

| Field | Type | Default |
|-------|------|---------|
| `use_datetime` | `bool` | `False` |
| `path_exists_function` | `str` | `"jsonb_path_exists"` |
| `path_exists_tz_function` | `str` | `"jsonb_path_exists_tz"` |
| `sort_field_types` | `Mapping[str, JSONSortScalarType]` | `{}` |

Notes:

- PostgreSQL function names are validated as SQL identifiers
- invalid names such as `jsonb_path_exists;DROP_TABLE` are rejected at config
  construction time
- `sort_field_types` keys are normalized and stored immutably

## JSONSortScalarType

Supported values:

- `TEXT`
- `INTEGER`
- `FLOAT`
- `NUMERIC`
- `BOOLEAN`
- `DATE`
- `TIME`
- `DATETIME`
- `DATETIME_TZ`

## ParseLimits defaults

| Field | Default |
|-------|---------|
| `max_query_length` | `4096` |
| `max_selector_length` | `256` |
| `max_argument_length` | `1024` |
| `max_arguments_per_list` | `100` |
| `max_expression_depth` | `16` |
| `max_node_count` | `1024` |

These limits exist for both robustness and security hardening.

## SortLimits defaults

| Field | Default |
|-------|---------|
| `max_sort_length` | `4096` |
| `max_fields` | `32` |
| `max_field_path_length` | `256` |

These limits bound sort-parser complexity and request-surface size.
