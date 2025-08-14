# Contributing to jinpy-utils

Thanks for your interest in contributing!

## Development Setup

1. Install Python 3.12+
2. Install [uv](https://github.com/astral-sh/uv)
3. Clone and install dependencies:

```bash
git clone https://github.com/jinto-ag/jinpy-utils.git
cd jinpy-utils
uv sync --all-extras
uv run pre-commit install
```

## Commands

- Format: `uv run ruff format .`
- Lint: `uv run ruff check --fix .`
- Types: `uv run mypy .`
- Tests: `uv run pytest`

## Pull Requests

- Create a topic branch: `feat/*` or `fix/*`
- Write conventional commits (e.g., `feat(logger): add file backend`)
- Include/adjust tests and docs
- Ensure CI is green (lint, types, tests)

## Code Style

- PEP 8, mypy (strict), ruff
- Keep functions small, single-responsibility
- Avoid suppressing lints unless justified with comments

## Security

- Avoid secrets in code; use GitHub secrets and environment variables
- Prefer least-privilege defaults
