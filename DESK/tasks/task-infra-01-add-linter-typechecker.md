# task-infra-01 - add linter and type-checker configs

## Goal

No linter (ruff, flake8) or type-checker (mypy, pyright) configuration exists. Code quality cannot be enforced mechanically. Coding standards are aspirational rather than checkable.

## Objective

Add configuration files for at least one linter and one type checker, aligned with the existing `docs/coding_standards.md`.

## Non-Goals

- fixing all existing lint/type violations in this task
- adding CI or pre-commit hooks
- adding GitHub Actions

## Documentation References

- `docs/coding_standards.md`

## References

- (no code changes needed, only config files)

## Exact Files To Change

- `pyproject.toml` — add tool config (or create `ruff.toml`, `mypy.ini`)
- `.gitignore` — add cache dirs (`.mypy_cache/`, `.ruff_cache/`)

## Files To Avoid Unless Necessary

- any source or test file

## Delete / Migrate Decision

- N/A (new config files, no migration)

## End State

Running `ruff check src/` and `mypy src/` produces output (possibly with violations) instead of "no config found" errors.

## Exit Criteria

- `ruff check src/` runs without error
- `mypy src/` runs without error

## Suggested Implementation Path

1. Create `pyproject.toml` with `[tool.ruff]` and `[tool.mypy]` sections
2. Add cache dirs to `.gitignore`
3. Verify both tools execute against the source tree

## Validation

- `ruff check src/` (may flag violations — that's OK, the tool works)
- `mypy src/` (may flag violations — that's OK, the tool works)

## Failure Modes

- config conflicts with existing implicit setuptools build
- tool version incompatibility with Python 3.10
