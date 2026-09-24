# task-infra-02 - add coverage measurement

## Goal

There is no test coverage measurement. Without it, gaps in test coverage are invisible, and refactoring carries unknown risk.

## Objective

Add coverage.py configuration and add `coverage` to the development dependencies.

## Non-Goals

- enforcing a coverage threshold or CI gate
- adding coverage reporting to CI

## Documentation References

- `docs/coding_standards.md`

## References

- (no code changes)

## Exact Files To Change

- `.coveragerc` or `pyproject.toml` — add coverage config
- `.gitignore` — add `htmlcov/`, `.coverage`

## Files To Avoid Unless Necessary

- any source or test file

## Delete / Migrate Decision

- N/A (new config)

## End State

Running `coverage run -m pytest && coverage report` produces a per-module coverage report.

## Exit Criteria

- `coverage run -m pytest -q` succeeds
- `coverage report` shows module-level percentages

## Suggested Implementation Path

1. Install coverage.py (`pip install coverage`)
2. Add `.coveragerc` with source path pointing to `src/`
3. Add `htmlcov/` and `.coverage` to `.gitignore`
4. Run and record the baseline

## Validation

- `coverage run -m pytest -q && coverage report`

## Failure Modes

- coverage config includes unwanted paths (`tests/`, `prototypes/`)
- coverage measurement affects test behavior (rare)
