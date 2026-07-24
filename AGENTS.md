# Agent Instructions

## CI Compliance

Always run the full CI quality suite at the end of every task implementation:

```bash
cd service
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest --tb=short --cov=. --cov-report=term-missing -q
```

Fix any failures before marking the task as complete. This ensures every commit
on the branch maintains CI quality gates.
