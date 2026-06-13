# Contributing

## Setup

```bash
git clone https://github.com/wskr00/pyrsql.git
cd pyrsql
uv sync --all-extras
```

## Development workflow

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy                  # type check
uv run pytest                # tests
```

## Project standards

- Google Python Style Guide
- strict mypy type checking
- ruff for linting and formatting
- pytest with `unit`, `integration`, `functional`, `performance` layers
- ORM-neutral core - zero ORM imports in `pyrsql.core`, `pyrsql.parsing`, `pyrsql.semantic`, `pyrsql.sorting`

## Test layers

| Layer | Purpose | Run with |
|-------|---------|----------|
| `unit` | Isolated module/class tests | `pytest tests/unit/` |
| `integration` | Cross-component pipelines | `pytest tests/integration/` |
| `functional` | Public API behavior | `pytest tests/functional/` |
| `performance` | Hotspot benchmarks | `pytest tests/performance/` |

## Docs

```bash
uv run mkdocs serve     # live preview at http://localhost:8000
uv run mkdocs build     # build static site
```

## Pull requests

- Keep PRs focused - one feature or fix per PR
- Update docs if the public API changes
- Run `ruff check . && mypy && pytest` before pushing
- Performance PRs should include benchmark results
