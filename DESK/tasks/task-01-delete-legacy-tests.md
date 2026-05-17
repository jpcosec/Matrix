# task-01 - Delete Legacy Tests

## Goal

Remove tests that only preserve the old runtime architecture.

## Objective

Delete or quarantine legacy tests so the active suite reflects the new operational model.

## Non-Goals

- Do not migrate runtime code in this task.
- Do not recreate legacy behavior in the new model.

## Pills Required

- `pill-04-legacy-migration-policy.md`
- `pill-07-task-granularity-and-parallelism.md`

## References

- `DESK/tasks/task-00-legacy-inventory.md`
- `tests/test_tkm_roundtrip_suite.py`
- `tests/test_tkm_implementation.py`
- `tests/test_wikipedia_solar_system.py`
- `tests/test_tkm_atom_map.py`
- `tests/test_whitepaper_ingestion.py`
- `tests/test_dimensional_collapse.py`
- `tests/test_tkm_orchestration.py`
- `tests/test_unified.py`
- `tests/test_matrix_engine.py`

## Exact Files To Change

- the legacy test files listed above
- `DESK/tasks/Board.md`

## Files To Avoid Unless Necessary

- `src/operational_model/**`

## Delete / Migrate Decision

- Delete tests that exist only for legacy runtime behavior.
- Rewrite only the tests whose algorithmic intent still matters for the new model.
- Execute this by file, not by slogan.

## End State

The active test suite points at the new architecture, not the old one.

## Exit Criteria

- Legacy-only test files are removed.
- Replacement tests exist for any migrated algorithmic capability worth keeping.

## Suggested Implementation Path

1. Remove obviously legacy acceptance tests.
2. Preserve only algorithmic intent as fresh tests on new modules.
3. Re-run the remaining suite.

## Validation

- `pytest tests/test_operational_model.py`
- any new focused tests created during migration

## Failure Modes

- Keeping a legacy test because it still passes.
- Rewriting a test against compatibility shims instead of the new architecture.
