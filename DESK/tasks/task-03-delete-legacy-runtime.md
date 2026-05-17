# task-03 - Delete Legacy Runtime

## Goal

Remove the old runtime once useful behavior has been migrated.

## Objective

Delete `UnifiedMatrixEngine` and the remaining legacy modules after their useful parts have either moved or been intentionally discarded.

## Non-Goals

- Do not preserve compatibility imports.
- Do not keep legacy code as dead backup inside `src/`.

## Pills Required

- `pill-04-legacy-migration-policy.md`
- `pill-07-task-granularity-and-parallelism.md`

## References

- `DESK/tasks/task-00-legacy-inventory.md`
- `DESK/tasks/task-02-migrate-useful-legacy-capabilities.md`
- `src/unified_engine.py`
- `src/unified_engine_core/**`
- `src/tkm_orchestrator.py`
- `src/matrix_engine.py`
- `src/boolean_matrix_engine.py`
- `src/context_composition.py`
- `src/subcontext_routing.py`
- `src/multivalued_engine.py`

## Exact Files To Change

- all legacy runtime files scheduled for deletion
- `DESK/tasks/Board.md`

## Files To Avoid Unless Necessary

- validated new-model modules not involved in compatibility removal

## Delete / Migrate Decision

- Delete every remaining legacy runtime file whose behavior is either migrated or intentionally dropped.

## End State

The repository runtime is the new architecture only.

## Exit Criteria

- `unified_engine` and other retired runtime files are gone.
- Remaining imports point only at the new codebase.
- Active tests cover only the new architecture.

## Suggested Implementation Path

1. Confirm task-02 completion for each migration candidate.
2. Remove last legacy imports.
3. Delete legacy modules.
4. Re-run the active suite.

## Validation

- `pytest tests/test_operational_model.py`
- any new focused tests created for migrated algorithms

## Failure Modes

- Leaving compatibility shims behind as hidden architecture.
- Deleting a runtime capability before a needed replacement exists.
