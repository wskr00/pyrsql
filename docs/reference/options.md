# Options Reference

## QueryOptions

| Field | Type | Default |
|-------|------|---------|
| `strict_equality` | `bool` | `False` |
| `distinct` | `bool` | `False` |
| `like_escape_character` | `str\|None` | `None` |
| `field_mapping` | `Mapping[str,str]` | `{}` |
| `model_field_mapping` | `Mapping[type,Mapping[str,str]]` | `{}` |
| `join_hints` | `Mapping[str,JoinHint]` | `{}` |
| `field_whitelist` | `frozenset[str]` | `frozenset()` |
| `field_blacklist` | `frozenset[str]` | `frozenset()` |
| `model_field_whitelist` | `Mapping[type,frozenset[str]]` | `{}` |
| `model_field_blacklist` | `Mapping[type,frozenset[str]]` | `{}` |
| `procedure_whitelist` | `tuple[str,...]` | `()` |
| `procedure_blacklist` | `tuple[str,...]` | `()` |
| `parse_limits` | `ParseLimits` | `DEFAULT_PARSE_LIMITS` |
| `operator_registry` | `OperatorRegistry` | `DEFAULT_OPERATOR_REGISTRY` |
| `custom_predicates` | `Mapping[str,CustomPredicateDefinition]` | `{}` |
| `value_converter_registry` | `ValueConverterRegistry` | `DEFAULT_*` |
| `field_value_converters` | `Mapping[str,ValueConverter]` | `{}` |
| `model_field_value_converters` | `Mapping[type,Mapping[str,ValueConverter]]` | `{}` |
| `json_options` | `JSONOptions` | `DEFAULT_JSON_OPTIONS` |

## SortOptions

| Field | Type | Default |
|-------|------|---------|
| `field_mapping` | `Mapping[str,str]` | `{}` |
| `model_field_mapping` | `Mapping[type,Mapping[str,str]]` | `{}` |
| `join_hints` | `Mapping[str,JoinHint]` | `{}` |
| `field_whitelist` | `frozenset[str]` | `frozenset()` |
| `field_blacklist` | `frozenset[str]` | `frozenset()` |
| `model_field_whitelist` | `Mapping[type,frozenset[str]]` | `{}` |
| `model_field_blacklist` | `Mapping[type,frozenset[str]]` | `{}` |
| `procedure_whitelist` | `tuple[str,...]` | `()` |
| `procedure_blacklist` | `tuple[str,...]` | `()` |
| `sort_limits` | `SortLimits` | `DEFAULT_SORT_LIMITS` |
| `json_options` | `JSONOptions` | `DEFAULT_JSON_OPTIONS` |

## JSONOptions

| Field | Type | Default |
|-------|------|---------|
| `use_datetime` | `bool` | `False` |
| `path_exists_function` | `str` | `"jsonb_path_exists"` |
| `path_exists_tz_function` | `str` | `"jsonb_path_exists_tz"` |
| `sort_field_types` | `Mapping[str,JSONSortScalarType]` | `{}` |

## JSONSortScalarType

`TEXT`, `INTEGER`, `FLOAT`, `NUMERIC`, `BOOLEAN`, `DATE`, `TIME`,
`DATETIME`, `DATETIME_TZ`.

## ParseLimits defaults

| Field | Default |
|-------|---------|
| `max_query_length` | 4096 |
| `max_selector_length` | 256 |
| `max_argument_length` | 1024 |
| `max_arguments_per_list` | 100 |
| `max_expression_depth` | 16 |
| `max_node_count` | 1024 |
